"""H-046: Livermore pivotal-point break with volume expansion and fail-fast exit (1h).

Entry (signal at close of bar t, fill at open of t+1), all must hold:
  close > 1.002 * P, P = highest high of the prior 240 bars (current excluded)
  volume >= 2.0 * mean volume of the previous 48 bars (current excluded)
  close > SMA(480) of close
Exit (decided in custom_exit on closed candles, fill at next open):
  bars t+1..t+8: close < P_entry (pivot of the signal bar) -> exit
  bar t+9 onward: close < lowest low of the prior 48 bars (current excluded)
Stop-loss 4% (native), cooldown 12 candles after any exit.
"""

from datetime import timedelta

from pandas import DataFrame
from freqtrade.strategy import IStrategy


class LivermorePivotFailFast_H046_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.04
    startup_candle_count = 600

    pivot_lookback = 240
    pivot_margin = 0.002
    volume_lookback = 48
    volume_multiple = 2.0
    trend_bars = 480
    fail_fast_bars = 8
    trail_lookback = 48

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 12}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["pivot"] = dataframe["high"].rolling(self.pivot_lookback).max().shift(1)
        dataframe["vol_avg"] = dataframe["volume"].rolling(self.volume_lookback).mean().shift(1)
        dataframe["sma480"] = dataframe["close"].rolling(self.trend_bars).mean()
        dataframe["trail_low"] = dataframe["low"].rolling(self.trail_lookback).min().shift(1)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe["close"] > (1.0 + self.pivot_margin) * dataframe["pivot"])
                & (dataframe["volume"] >= self.volume_multiple * dataframe["vol_avg"])
                & (dataframe["close"] > dataframe["sma480"])
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "livermore_pivot_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on the entry bar of the trade; handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0:
            return None
        step = timedelta(hours=1)
        closed = dataframe[dataframe["date"] + step <= current_time]
        if len(closed) == 0:
            return None
        last = closed.iloc[-1]
        signal_date = trade.open_date_utc - step
        n = int(round((last["date"] - signal_date) / step))
        if n < 1 or last["volume"] <= 0:
            return None
        if n <= self.fail_fast_bars:
            sig = closed[closed["date"] == signal_date]
            if len(sig) == 0:
                return None
            pivot = sig.iloc[-1]["pivot"]
            if pivot == pivot and last["close"] < pivot:
                return "fail_fast_pivot"
            return None
        trail = last["trail_low"]
        if trail == trail and last["close"] < trail:
            return "trail_48_low"
        return None
