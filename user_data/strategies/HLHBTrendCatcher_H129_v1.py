"""H-129: HLHB trend catcher on 15m.

Rule (research/proposals/H-129.json), 15m, closed bars only, long only, spot:
- EMA5 / EMA10 of close; RSI10 = Wilder RSI of the median price (high+low)/2; ADX14.
- Vmean(t) = mean volume of bars t-20..t-1 (current bar excluded).
- ENTRY at the close of bar t when ALL hold:
  EMA5 crosses above EMA10 on bar t, RSI10 crosses above 50 on bar t, ADX14 > 25,
  volume(t) >= 1.5 x Vmean(t). The order fills at the next 15m open.
- EXITS, first one wins:
  (a) fixed stop -1.5% (native stoploss, intrabar);
  (b) trailing stop: active once the high reached +1.9%, then 1.2% below the highest price;
  (c) mirror signal: EMA5 crosses below EMA10 and RSI10 crosses below 50 on the same bar;
  (d) time exit: 12 hours (48 bars) after the fill, in custom_exit.
- No take-profit and no ROI. Warm-up 400 bars.
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy

EMA_FAST = 5
EMA_SLOW = 10
RSI_LENGTH = 10
RSI_LEVEL = 50.0
ADX_LENGTH = 14
ADX_MIN = 25.0
VOLUME_MEAN_BARS = 20
VOLUME_MULT = 1.5
TIME_EXIT_HOURS = 12  # 48 bars of 15m


class HLHBTrendCatcher_H129_v1(IStrategy):
    """EMA5/10 cross + RSI10(median price) cross of 50 + ADX14 > 25 + volume 1.5x, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.015
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.019
    trailing_only_offset_is_reached = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = pd.Series(ta.EMA(dataframe, timeperiod=EMA_FAST), index=dataframe.index).astype(float)
        dataframe["ema_slow"] = pd.Series(ta.EMA(dataframe, timeperiod=EMA_SLOW), index=dataframe.index).astype(float)
        median_price = (dataframe["high"] + dataframe["low"]) / 2.0
        mp_frame = DataFrame({"close": median_price}, index=dataframe.index)
        dataframe["rsi_mp"] = pd.Series(ta.RSI(mp_frame, timeperiod=RSI_LENGTH), index=dataframe.index).astype(float)
        dataframe["adx"] = pd.Series(ta.ADX(dataframe, timeperiod=ADX_LENGTH), index=dataframe.index).astype(float)
        # mean volume of the previous 20 bars; the current bar is excluded
        dataframe["vmean"] = dataframe["volume"].shift(1).rolling(VOLUME_MEAN_BARS).mean()
        dataframe["ema_fast_prev"] = dataframe["ema_fast"].shift(1)
        dataframe["ema_slow_prev"] = dataframe["ema_slow"].shift(1)
        dataframe["rsi_mp_prev"] = dataframe["rsi_mp"].shift(1)
        return dataframe

    def _defined(self, dataframe: DataFrame) -> pd.Series:
        cols = ["ema_fast", "ema_slow", "ema_fast_prev", "ema_slow_prev", "rsi_mp", "rsi_mp_prev"]
        return dataframe[cols].notna().all(axis=1) & (dataframe["volume"] > 0)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_cross_up = (dataframe["ema_fast"] > dataframe["ema_slow"]) & (
            dataframe["ema_fast_prev"] <= dataframe["ema_slow_prev"]
        )
        rsi_cross_up = (dataframe["rsi_mp"] > RSI_LEVEL) & (dataframe["rsi_mp_prev"] <= RSI_LEVEL)
        adx_ok = dataframe["adx"].notna() & (dataframe["adx"] > ADX_MIN)
        volume_ok = dataframe["vmean"].notna() & (dataframe["volume"] >= VOLUME_MULT * dataframe["vmean"])
        signal = self._defined(dataframe) & ema_cross_up & rsi_cross_up & adx_ok & volume_ok
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "ema_rsi_cross_adx_vol")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ema_cross_down = (dataframe["ema_fast"] < dataframe["ema_slow"]) & (
            dataframe["ema_fast_prev"] >= dataframe["ema_slow_prev"]
        )
        rsi_cross_down = (dataframe["rsi_mp"] < RSI_LEVEL) & (dataframe["rsi_mp_prev"] >= RSI_LEVEL)
        signal = self._defined(dataframe) & ema_cross_down & rsi_cross_down
        dataframe.loc[signal, ["exit_long", "exit_tag"]] = (1, "mirror_cross_down")
        return dataframe

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
