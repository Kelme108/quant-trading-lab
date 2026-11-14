"""H-139: Dual Thrust long-only on 1h candles.

For UTC day D: O = open of the 00:00 bar. From the 4 completed days D-4..D-1:
HH/LL = highest daily high / lowest daily low, HC/LC = highest / lowest daily
close (close of the 23:00 bar). RANGE = max(HH - LC, HC - LL),
UPPER = O + 0.5 * RANGE, LOWER = O - 0.5 * RANGE. Armed only if
0.5 * RANGE / O >= 0.01. Filter: the latest completed 4h bar (UTC blocks
00,04,..,20 built from 1h bars) closes above the SMA(50) of 4h closes.
Entry at the close of a 00:00..17:00 bar when close > UPPER, armed and the
filter holds; one entry per UTC day. Exit when a bar closes below LOWER, on
the 23:00 bar (day end), or after 12 hours (custom_exit). Native stop 5%.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class DualThrustIntraday_H139_v1(IStrategy):
    """Open-anchored 4-day-range breakout, flat by day end or after 12 hours."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    startup_candle_count = 300

    range_days = 4
    k_upper = 0.5
    k_lower = 0.5
    min_half_range_over_open = 0.01
    filter_sma_length = 50
    first_hour = 0
    last_hour = 17
    day_end_hour = 23
    time_exit_hours = 12

    @property
    def protections(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = pd.to_datetime(dataframe["date"])
        day = date.dt.floor("D")
        hour = date.dt.hour

        # ---- Daily candles from completed UTC days (24 bars) ----
        helper = pd.DataFrame(
            {
                "day": day,
                "high": dataframe["high"],
                "low": dataframe["low"],
                "open0": dataframe["open"].where(hour == 0),
                "close23": dataframe["close"].where(hour == 23),
            }
        )
        grouped = helper.groupby("day")
        daily = pd.DataFrame(
            {
                "high": grouped["high"].max(),
                "low": grouped["low"].min(),
                "n": grouped["high"].count(),
                "open0": grouped["open0"].max(),
                "close23": grouped["close23"].max(),
            }
        )
        full_days = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
        daily = daily.reindex(full_days)
        complete = daily["n"] == 24
        d_high = daily["high"].where(complete)
        d_low = daily["low"].where(complete)
        d_close = daily["close23"].where(complete)

        n_days = self.range_days
        # Previous N completed days (shifted by one day), NaN if any is missing.
        hh = d_high.shift(1).rolling(n_days).max()
        ll = d_low.shift(1).rolling(n_days).min()
        hc = d_close.shift(1).rolling(n_days).max()
        lc = d_close.shift(1).rolling(n_days).min()
        day_range = np.maximum(hh - lc, hc - ll)

        day_open = daily["open0"]
        dataframe["day_open"] = day_open.reindex(day).astype(float).values
        dataframe["range_4d"] = day_range.reindex(day).astype(float).values
        dataframe["upper"] = dataframe["day_open"] + self.k_upper * dataframe["range_4d"]
        dataframe["lower"] = dataframe["day_open"] - self.k_lower * dataframe["range_4d"]
        dataframe["half_range_ratio"] = (
            self.k_upper * dataframe["range_4d"] / dataframe["day_open"]
        )

        # ---- 4h filter built from 1h bars ----
        block = date.dt.floor("4h")
        bhelper = pd.DataFrame(
            {
                "block": block,
                "n": dataframe["close"],
                "close3": dataframe["close"].where((hour % 4) == 3),
            }
        )
        bgrouped = bhelper.groupby("block")
        h4 = pd.DataFrame(
            {"n": bgrouped["n"].count(), "close": bgrouped["close3"].max()}
        )
        full_blocks = pd.date_range(h4.index.min(), h4.index.max(), freq="4h")
        h4 = h4.reindex(full_blocks)
        h4_close = h4["close"].where(h4["n"] == 4)
        h4_sma = h4_close.rolling(self.filter_sma_length).mean()
        h4_ok = (h4_close > h4_sma).astype(float).where(h4_sma.notna() & h4_close.notna())

        # Latest 4h bar completed at or before the close of the signal bar.
        usable_block = (date + pd.Timedelta(hours=1)).dt.floor("4h") - pd.Timedelta(
            hours=4
        )
        dataframe["filter_4h"] = h4_ok.reindex(usable_block).astype(float).values

        dataframe["hour_utc"] = hour.values
        dataframe["day_utc"] = day
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["upper"].notna()
            & dataframe["lower"].notna()
            & dataframe["half_range_ratio"].notna()
            & dataframe["filter_4h"].notna()
        )
        cond = (
            defined
            & (dataframe["hour_utc"] >= self.first_hour)
            & (dataframe["hour_utc"] <= self.last_hour)
            & (dataframe["close"] > dataframe["upper"])
            & (dataframe["half_range_ratio"] >= self.min_half_range_over_open)
            & (dataframe["filter_4h"] == 1.0)
            & (dataframe["volume"] > 0)
        )
        # One entry per UTC day: only the first qualifying bar may signal.
        order = cond.astype(int).groupby(dataframe["day_utc"]).cumsum()
        first = cond & (order == 1)
        dataframe.loc[first, ["enter_long", "enter_tag"]] = (1, "dual_thrust_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        below_lower = dataframe["lower"].notna() & (
            dataframe["close"] < dataframe["lower"]
        )
        day_end = dataframe["hour_utc"] == self.day_end_hour
        active = dataframe["volume"] > 0
        dataframe.loc[
            (below_lower & active), ["exit_long", "exit_tag"]
        ] = (1, "close_below_lower")
        dataframe.loc[
            (day_end & active & ~below_lower), ["exit_long", "exit_tag"]
        ] = (1, "day_end")
        return dataframe

    def custom_exit(
        self, pair, trade, current_time, current_rate, current_profit, **kwargs
    ):
        if current_time - trade.open_date_utc >= timedelta(hours=self.time_exit_hours):
            return "time_exit_12h"
        return None
