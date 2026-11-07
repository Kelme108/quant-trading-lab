"""H-069: US cash-open 15m opening-range breakout on a DST-aware New York clock.

Rule (closed 15m bars; signals fill at the next bar open):
- Clock: every time is America/New_York local time converted from the candle's UTC open time (DST per date).
  Only Monday to Friday New York dates trade (no holiday calendar).
- Opening range: the single 15m bar opening at 09:30 ET on that New York date; ORH = its high, ORL = its low.
  No such bar -> no trade that day. ORH/ORL are frozen for the day (carried forward only, never backwards).
- Armed day: 0.003 <= (ORH - ORL) / ORL <= 0.025.
- Entry: on an armed day, the FIRST bar of that New York date opening between 09:45 and 14:30 ET inclusive whose
  close > ORH. Later bars of the day never signal (at most one trade per day, no re-entry).
- Exit (first of):
  (a) a bar of the entry day closes below ORL;
  (b) time exit: any bar opening at or after 15:45 ET on the entry date, or any bar on a later date.
  Signals are stateless, so (b) is expressed as: bar opens >= 15:45 ET, or before 09:45 ET, or on a weekend date.
  A position can only have been opened on the current date after a bar opening >= 09:45 ET closed, so any bar
  before 09:45 ET or on a weekend belongs to a later date than the entry date.
- Stop-loss: fixed 3.0% native intrabar stop. No take-profit, no cooldown beyond one trade per day.
"""

import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

NY_TZ = "America/New_York"
OR_BAR_MIN = 9 * 60 + 30          # 09:30 ET
ENTRY_FIRST_MIN = 9 * 60 + 45     # 09:45 ET
ENTRY_LAST_MIN = 14 * 60 + 30     # 14:30 ET
TIME_EXIT_MIN = 15 * 60 + 45      # 15:45 ET
MIN_RANGE_FRAC = 0.003
MAX_RANGE_FRAC = 0.025


class SessionOpeningRangeBreakout_H069_v1(IStrategy):
    """Breakout of the 09:30 ET 15m opening range, flat by the 16:00 ET close."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    startup_candle_count = 96

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dates = pd.to_datetime(dataframe["date"])
        if dates.dt.tz is None:
            dates = dates.dt.tz_localize("UTC")
        ny = dates.dt.tz_convert(NY_TZ)
        day_key = ny.dt.strftime("%Y-%m-%d")

        dataframe["ny_minutes"] = ny.dt.hour * 60 + ny.dt.minute
        dataframe["ny_weekday"] = ny.dt.day_of_week

        is_or_bar = dataframe["ny_minutes"] == OR_BAR_MIN
        # Carry the 09:30 ET bar's high/low forward within the same New York date only (backward-looking).
        or_high_raw = dataframe["high"].where(is_or_bar)
        or_low_raw = dataframe["low"].where(is_or_bar)
        dataframe["or_high"] = or_high_raw.groupby(day_key).ffill()
        dataframe["or_low"] = or_low_raw.groupby(day_key).ffill()

        range_frac = (dataframe["or_high"] - dataframe["or_low"]) / dataframe["or_low"]
        armed = (range_frac >= MIN_RANGE_FRAC) & (range_frac <= MAX_RANGE_FRAC)

        in_window = (dataframe["ny_minutes"] >= ENTRY_FIRST_MIN) & (dataframe["ny_minutes"] <= ENTRY_LAST_MIN)
        weekday = dataframe["ny_weekday"] < 5
        breakout = (armed & in_window & weekday & (dataframe["close"] > dataframe["or_high"])).fillna(False)

        # Only the first qualifying bar of the New York date counts (cumulative count looks back only).
        breakout_count = breakout.astype(int).groupby(day_key).cumsum()
        dataframe["first_breakout"] = (breakout & (breakout_count == 1)).astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            (dataframe["first_breakout"] == 1)
            & dataframe["or_high"].notna()
            & dataframe["or_low"].notna()
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[cond, ["enter_long", "enter_tag"]] = (1, "us_orb_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        minutes = dataframe["ny_minutes"]
        below_orl = dataframe["or_low"].notna() & (dataframe["close"] < dataframe["or_low"])
        time_exit = (
            (minutes >= TIME_EXIT_MIN)
            | (minutes < ENTRY_FIRST_MIN)
            | (dataframe["ny_weekday"] >= 5)
        )
        vol_ok = dataframe["volume"] > 0

        dataframe.loc[below_orl & vol_ok, ["exit_long", "exit_tag"]] = (1, "close_below_orl")
        dataframe.loc[time_exit & ~below_orl & vol_ok, ["exit_long", "exit_tag"]] = (1, "time_exit")
        return dataframe
