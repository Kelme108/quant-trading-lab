"""H-091: fast RSI(2) dip above the 200-candle mean on closed 2h candles, flat within the day.

2h candles are built from the 1h frame (UTC blocks 00,02,...,22). A 2h candle is
complete only on the 1h bar opening at an odd hour (01,...,23), whose close is the
2h close. Signals are set only on those bars and fill at the next 1h open.

Rules:
- RSI2 = Wilder RSI(2) on 2h closes (alpha 1/2, seeded with the simple average of
  the first 2 changes); SMA200 and SMA5 of 2h closes.
- Entry: 2h close > SMA200 AND RSI2 < 10 AND fill bar opens 00:00-16:00 UTC;
  at most 2 entries per pair per UTC day (confirm_trade_entry).
- Exit signal: 2h close > SMA5 OR 2h close < SMA200.
- 2% stop via stoploss. Time exit in custom_exit: sale at the 23:00 UTC open or
  at the open of the 12th 1h bar after the entry bar, whichever comes first.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy


def wilder_rsi(values: np.ndarray, length: int) -> np.ndarray:
    """Wilder RSI, seeded with the simple average of the first `length` changes."""
    out = np.full(len(values), np.nan)
    if len(values) <= length:
        return out
    change = np.diff(values)
    gain = np.where(change > 0, change, 0.0)
    loss = np.where(change < 0, -change, 0.0)
    avg_gain = gain[:length].mean()
    avg_loss = loss[:length].mean()
    for i in range(length, len(values)):
        if i > length:
            avg_gain = (avg_gain * (length - 1) + gain[i - 1]) / length
            avg_loss = (avg_loss * (length - 1) + loss[i - 1]) / length
        if avg_loss == 0:
            out[i] = 100.0 if avg_gain > 0 else 50.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


class DailyRSI2Dip_H091_v1(IStrategy):
    """RSI(2) dip buy on 2h closes inside a 200-candle uptrend, day-trade frame."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    startup_candle_count = 800

    rsi_length = 2
    rsi_entry_below = 10
    trend_sma_length = 200
    exit_sma_length = 5
    max_entries_per_day = 2
    max_hold_hours = 12
    forced_exit_hour = 23
    last_fill_hour = 16

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        date = dataframe["date"]
        # 2h block is complete on the odd-hour bar whose predecessor is the even-hour bar.
        complete = (date.dt.hour % 2 == 1) & (
            (date - date.shift(1)) == pd.Timedelta(hours=1)
        )
        close2 = dataframe["close"].where(complete).dropna()
        values = close2.to_numpy(dtype=float)

        rsi = pd.Series(wilder_rsi(values, self.rsi_length), index=close2.index)
        sma_trend = close2.rolling(self.trend_sma_length).mean()
        sma_exit = close2.rolling(self.exit_sma_length).mean()

        dataframe["close_2h"] = close2.reindex(dataframe.index)
        dataframe["rsi2_2h"] = rsi.reindex(dataframe.index)
        dataframe["sma200_2h"] = sma_trend.reindex(dataframe.index)
        dataframe["sma5_2h"] = sma_exit.reindex(dataframe.index)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fill_hour = (dataframe["date"] + pd.Timedelta(hours=1)).dt.hour
        dataframe.loc[
            (
                dataframe["close_2h"].notna()
                & dataframe["rsi2_2h"].notna()
                & dataframe["sma200_2h"].notna()
                & (dataframe["close_2h"] > dataframe["sma200_2h"])
                & (dataframe["rsi2_2h"] < self.rsi_entry_below)
                & (fill_hour <= self.last_fill_hour)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "rsi2_dip_2h")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                dataframe["close_2h"].notna()
                & dataframe["sma5_2h"].notna()
                & dataframe["sma200_2h"].notna()
                & (
                    (dataframe["close_2h"] > dataframe["sma5_2h"])
                    | (dataframe["close_2h"] < dataframe["sma200_2h"])
                )
                & (dataframe["volume"] > 0)
            ),
            ["exit_long", "exit_tag"],
        ] = (1, "above_sma5_or_below_sma200")
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        if current_time.hour >= self.forced_exit_hour:
            return "time_2300"
        if current_time - trade.open_date_utc >= timedelta(hours=self.max_hold_hours):
            return "time_12h"
        return None

    def confirm_trade_entry(
        self, pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side, **kwargs
    ):
        from freqtrade.persistence import Trade

        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        trades = Trade.get_trades_proxy(pair=pair, open_date=day_start)
        today = [t for t in trades if t.open_date_utc >= day_start]
        return len(today) < self.max_entries_per_day
