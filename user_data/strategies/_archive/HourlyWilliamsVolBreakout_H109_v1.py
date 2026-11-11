"""H-109: Crabel stretch breakout at the Asia, Europe and US session opens (15m, long only).

Sessions (UTC, bar open times): A 00:00-07:45 (32 bars), E 08:00-13:15 (22 bars), U 13:30-23:45 (42 bars).
O = open of the session's first bar. NOISE of a completed session = min(H - O, O - L) / O.
STRETCH S = 2.0 x mean NOISE of the 10 most recent completed sessions of the same type (days D-10..D-1).
No trade if any of those 10 sessions or the current session's first bar is missing a bar, or if S <= 0.

Entry: the FIRST bar t of the session with close >= O x (1 + S); buy at the next open only if t lies in the
first half of the session (A: to 03:45, E: to 10:30, U: to 18:30). One trade per session.
Stop: P = min(O x (1 - S), 0.99 x entry fill), fixed at entry (custom_stoploss), never moved.
Native stoploss -0.15 is the backstop. Exit: close of the session's last bar (07:45, 13:15, 23:45), filled
at the next open; also built into custom_exit as a time exit.
"""

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


SESSION_START_MIN = (0, 480, 810)  # A 00:00, E 08:00, U 13:30
SESSION_BARS = (32, 22, 42)
SESSION_LAST_ENTRY_MIN = (225, 630, 1110)  # 03:45, 10:30, 18:30
SESSION_LAST_BAR_MIN = (465, 795, 1425)  # 07:45, 13:15, 23:45
SESSION_END_MIN = (480, 810, 1440)  # first minute after the session
NOISE_LOOKBACK = 10
STRETCH_MULTIPLE = 2.0
MIN_STOP_DISTANCE = 0.01
BACKSTOP = 0.15


def session_type_from_minutes(minutes):
    """0 = A (before 08:00), 1 = E (08:00-13:15), 2 = U (13:30 onward)."""
    return pd.Series(
        np.select([minutes < SESSION_START_MIN[1], minutes < SESSION_START_MIN[2]], [0, 1], 2),
        index=minutes.index,
    )


class HourlyWilliamsVolBreakout_H109_v1(IStrategy):
    """Stretch breakout in the first half of each of the three UTC sessions, flat at session end."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.15
    use_custom_stoploss = True
    startup_candle_count = 1100

    @property
    def protections(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"])
        day = date.dt.floor("D")
        minutes = date.dt.hour * 60 + date.dt.minute
        stype = session_type_from_minutes(minutes)

        sess_open = pd.Series(np.nan, index=dataframe.index)
        stretch = pd.Series(np.nan, index=dataframe.index)
        if len(dataframe) > 0:
            full_days = pd.date_range(day.min(), day.max(), freq="D")
        for k in range(3):
            sel = stype == k
            if not sel.any():
                continue
            helper = pd.DataFrame(
                {
                    "day": day[sel],
                    "high": dataframe["high"][sel],
                    "low": dataframe["low"][sel],
                    "open0": dataframe["open"][sel].where(minutes[sel] == SESSION_START_MIN[k]),
                }
            )
            grouped = helper.groupby("day")
            table = pd.DataFrame(
                {
                    "high": grouped["high"].max(),
                    "low": grouped["low"].min(),
                    "n": grouped["high"].count(),
                    "open0": grouped["open0"].max(),
                }
            ).reindex(full_days)
            complete = (table["n"] == SESSION_BARS[k]) & table["open0"].notna()
            noise = (
                np.minimum(table["high"] - table["open0"], table["open0"] - table["low"])
                / table["open0"]
            ).where(complete)
            # Same-type sessions on days D-10..D-1 only (current session excluded); any gap gives NaN.
            mean_noise = noise.rolling(NOISE_LOOKBACK).mean().shift(1)
            s_value = STRETCH_MULTIPLE * mean_noise
            s_value = s_value.where((s_value > 0) & table["open0"].notna())
            sess_open[sel] = day[sel].map(table["open0"]).astype(float).values
            stretch[sel] = day[sel].map(s_value).astype(float).values

        dataframe["minute_of_day"] = minutes.values
        dataframe["session_type"] = stype.values
        dataframe["day_utc"] = day
        dataframe["sess_open"] = sess_open.values
        dataframe["stretch"] = stretch.values
        dataframe["breakout_level"] = dataframe["sess_open"] * (1.0 + dataframe["stretch"])
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = dataframe["breakout_level"].notna() & dataframe["stretch"].notna()
        raw = defined & (dataframe["close"] >= dataframe["breakout_level"])
        # First qualifying bar of each session (volume is not part of the definition of "first").
        order = raw.astype(int).groupby([dataframe["day_utc"], dataframe["session_type"]]).cumsum()
        first = raw & (order == 1)

        last_entry = dataframe["session_type"].map(dict(enumerate(SESSION_LAST_ENTRY_MIN)))
        first_half = dataframe["minute_of_day"] <= last_entry

        cond = first & first_half & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "crabel_stretch_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        last_bar = dataframe["minute_of_day"].isin(SESSION_LAST_BAR_MIN)
        cond = last_bar & (dataframe["volume"] > 0)
        dataframe.loc[cond, ["exit_long", "exit_tag"]] = (1, "session_end")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        """Time exit: leave at the first candle at or after the end of the session the trade was opened in."""
        opened = pd.Timestamp(trade.open_date_utc)
        minutes = opened.hour * 60 + opened.minute
        k = 0 if minutes < SESSION_START_MIN[1] else (1 if minutes < SESSION_START_MIN[2] else 2)
        session_end = opened.normalize() + pd.Timedelta(minutes=SESSION_END_MIN[k])
        if pd.Timestamp(current_time) >= session_end:
            return "session_end"
        return None

    def custom_stoploss(
        self, pair, trade, current_time, current_rate, current_profit, after_fill=False, **kwargs
    ):
        """Fixed stop level P = min(O x (1 - S), 0.99 x entry), never moved, at most 15% below entry."""
        entry = trade.open_rate
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or len(frame) == 0:
            return self.stoploss
        signal_rows = frame[pd.to_datetime(frame["date"]) < pd.Timestamp(trade.open_date_utc)]
        if len(signal_rows) == 0:
            return self.stoploss
        row = signal_rows.iloc[-1]
        session_open = row["sess_open"]
        s_value = row["stretch"]
        if pd.isna(session_open) or pd.isna(s_value) or not current_rate > 0:
            return self.stoploss
        level = min(session_open * (1.0 - s_value), (1.0 - MIN_STOP_DISTANCE) * entry)
        level = max(level, (1.0 - BACKSTOP) * entry)
        if current_rate <= level:
            return -0.0001
        return -(1.0 - level / current_rate)
