"""H-108: Livermore pivotal-point break with volume burst, 2-bar fail-fast, intraday session-bounded (1h).

Entry (signal at close of bar t, fill at open of t+1), all must hold:
  close > 1.002 * P, P = highest high of the previous 20 bars (current excluded)
  volume >= 2.0 * mean volume of the previous 4 bars (current excluded)
  close > SMA(40) of close (current bar included)
  open hour of bar t between 0 and 16 UTC inclusive
Exit (decided in custom_exit on closed candles, fill at next open):
  bars t+1, t+2: close < P_entry (pivot of the signal bar) -> exit
  bar t+3 onward: close < lowest low of the previous 4 bars (current excluded)
  session flat: sold at the 23:00 UTC open (position open at the close of the 22:00 bar)
  max hold: sold at the open 12 hours after the fill
Stop-loss 2% (native), cooldown 1 candle after any exit.
"""

from datetime import timedelta

from pandas import DataFrame
import pandas as pd
from freqtrade.strategy import IStrategy


class LivermorePivotFailFast_H108_v1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    startup_candle_count = 100

    pivot_lookback = 20
    pivot_margin = 0.002
    volume_lookback = 4
    volume_multiple = 2.0
    trend_bars = 40
    fail_fast_bars = 2
    trail_lookback = 4
    entry_first_hour = 0
    entry_last_hour = 16
    session_flat_hour = 23
    max_hold_hours = 12

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": 1}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["pivot"] = dataframe["high"].rolling(self.pivot_lookback).max().shift(1)
        dataframe["vol_avg"] = dataframe["volume"].rolling(self.volume_lookback).mean().shift(1)
        dataframe["sma40"] = dataframe["close"].rolling(self.trend_bars).mean()
        dataframe["trail_low"] = dataframe["low"].rolling(self.trail_lookback).min().shift(1)
        if "date" in dataframe:
            dataframe["hour_utc"] = pd.to_datetime(dataframe["date"]).dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["pivot"].notna()
            & dataframe["vol_avg"].notna()
            & dataframe["sma40"].notna()
            & dataframe["hour_utc"].notna()
        )
        dataframe.loc[
            (
                defined
                & (dataframe["close"] > (1.0 + self.pivot_margin) * dataframe["pivot"])
                & (dataframe["volume"] >= self.volume_multiple * dataframe["vol_avg"])
                & (dataframe["close"] > dataframe["sma40"])
                & (dataframe["hour_utc"] >= self.entry_first_hour)
                & (dataframe["hour_utc"] <= self.entry_last_hour)
                & (dataframe["volume"] > 0)
            ),
            ["enter_long", "enter_tag"],
        ] = (1, "livermore_pivot_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on the entry bar of the trade; handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        # Calendar exits (clock only, no candle data).
        if current_time - trade.open_date_utc >= timedelta(hours=self.max_hold_hours):
            return "max_hold_12h"
        if (
            current_time.hour >= self.session_flat_hour
            or current_time.date() > trade.open_date_utc.date()
        ):
            return "session_flat_2300"

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
            return "trail_4_low"
        return None
