"""H-042: hourly inside-bar breakout of a wide mother bar (long only, 1h).

Rule (closed candles only, orders fill at the next open):
- Setup at the close of bar i: high[i] < high[i-1], low[i] > low[i-1],
  (high[i-1]-low[i-1])/low[i-1] >= 0.012 and close[i] > SMA(240).
  Mother bar M = bar i-1. Window = bars i+1..i+6. While a window is open no
  new setup is created; a setup is void once used or expired.
- Entry: first window bar t with close > high(M), if no position is open.
- Exit: first bar after the entry bar closing below the mother midpoint, or
  the 24th bar after the entry bar (sold at the following open).
- Stop: fixed 4% below entry (native stoploss, simulated here only to keep the
  position state in step with the engine).
"""

import numpy as np
import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class HourlyInsideBarBreakout_H042_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 300

    SMA_LEN = 240
    MIN_MOTHER_RANGE = 0.012
    WINDOW_BARS = 6
    MAX_HOLD_BARS = 24

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma_trend"] = ta.SMA(dataframe, timeperiod=self.SMA_LEN)

        n = len(dataframe)
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        opn = dataframe["open"].to_numpy(dtype=float)
        vol = dataframe["volume"].to_numpy(dtype=float)
        sma = dataframe["sma_trend"].to_numpy(dtype=float)

        entry = np.zeros(n, dtype=bool)
        exit_ = np.zeros(n, dtype=bool)

        setup_active = False
        setup_end = -1
        m_high = m_mid = 0.0
        in_pos = False
        entry_bar = -1
        entry_price = 0.0
        mid = 0.0

        for t in range(1, n):
            valid = (
                vol[t] > 0
                and not np.isnan(high[t])
                and not np.isnan(low[t])
                and not np.isnan(close[t])
            )
            if setup_active and t > setup_end:
                setup_active = False

            exited_now = False
            if in_pos:
                # simulated intrabar stop (entry bar onwards)
                if t >= entry_bar and low[t] <= entry_price * (1.0 + self.stoploss):
                    in_pos = False
                elif valid and t > entry_bar:
                    if close[t] < mid or t >= entry_bar + self.MAX_HOLD_BARS:
                        exit_[t] = True
                        in_pos = False
                        exited_now = True

            if not valid:
                continue

            if setup_active and not in_pos and not exited_now:
                if close[t] > m_high:
                    entry[t] = True
                    in_pos = True
                    entry_bar = t + 1
                    # next open is unknown on the final row; close is a proxy there
                    entry_price = opn[t + 1] if t + 1 < n else close[t]
                    mid = m_mid
                    setup_active = False
                continue
            if setup_active:
                continue

            m_range = (high[t - 1] - low[t - 1]) / low[t - 1] if low[t - 1] > 0 else np.nan
            if (
                not np.isnan(sma[t])
                and high[t] < high[t - 1]
                and low[t] > low[t - 1]
                and m_range >= self.MIN_MOTHER_RANGE
                and close[t] > sma[t]
            ):
                setup_active = True
                setup_end = t + self.WINDOW_BARS
                m_high = high[t - 1]
                m_mid = (high[t - 1] + low[t - 1]) / 2.0

        dataframe["ibb_entry"] = entry.astype(int)
        dataframe["ibb_exit"] = exit_.astype(int)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["ibb_entry"] == 1) & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "inside_bar_breakout")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["ibb_exit"] == 1) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "mother_midpoint_or_time")
        return dataframe
