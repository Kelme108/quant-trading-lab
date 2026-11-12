"""H-119: Kaufman efficiency-ratio thrust on 15m.

Rule (research/proposals/H-119.json), 15m, closed bars only, long only, spot:
- Signed ER(t) = (close(t) - close(t-10)) / sum_{i=0..9} |close(t-i) - close(t-i-1)|
  (ER = 0 when the denominator is 0). ATR(14) is the Wilder ATR.
- ENTRY at the close of bar t when ER(t-1) <= 0.6 and ER(t) > 0.6 and ATR(t)/close(t) >= 0.004.
  One position per pair is enforced by the engine; the order fills at the next 15m open (E).
- STOP (custom_stoploss, intrabar): S0 = min(lowest low of bars t-9..t, 0.99*E); after each later
  closed bar k, S = max(S, lowest low of bars k-9..k); never lowered. Native backstop -10%.
- TAKE-PROFIT +2% and TIME EXIT after 32 bars (8h) are done in custom_exit (minimal_roi is fixed
  by the contract at {"0": 100.0}).
- Warm-up 400 bars.
"""

from datetime import timedelta

import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy

ER_PERIOD = 10
ER_THRESHOLD = 0.6
ATR_PERIOD = 14
ATR_OVER_CLOSE_MIN = 0.004
STOP_LOOKBACK = 10
MIN_INITIAL_STOP_PCT = 0.01
TAKE_PROFIT_PCT = 0.02
TIME_EXIT_BARS = 32
BAR = timedelta(minutes=15)


class EfficiencyRatioThrust_H119_v1(IStrategy):
    """ER(10) crosses above 0.6, ATR filter, trailing 10-bar-low stop, +2% target, 8h exit."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    trailing_stop = False
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"].astype(float)
        path = close.diff().abs().rolling(ER_PERIOD).sum()
        net = close - close.shift(ER_PERIOD)
        er = (net / path.where(path > 0)).mask(path == 0, 0.0)
        dataframe["er"] = er
        dataframe["er_prev"] = er.shift(1)
        atr = pd.Series(ta.ATR(dataframe, timeperiod=ATR_PERIOD), index=dataframe.index).astype(float)
        dataframe["atr"] = atr
        dataframe["atr_ratio"] = atr / close
        # lowest low of the last 10 bars, current bar included (used for the stop)
        dataframe["low10"] = dataframe["low"].rolling(STOP_LOOKBACK).min()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe[["er", "er_prev", "atr_ratio"]].notna().all(axis=1)
            & (dataframe["volume"] > 0)
        )
        cross_up = (dataframe["er_prev"] <= ER_THRESHOLD) & (dataframe["er"] > ER_THRESHOLD)
        active = dataframe["atr_ratio"] >= ATR_OVER_CLOSE_MIN
        signal = defined & cross_up & active
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "er_cross_0.6")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No indicator exit: stop, target and time exit are handled by the engine/custom_exit.
        return dataframe

    def custom_stoploss(self, pair: str, trade, current_time, current_rate: float,
                        current_profit: float, **kwargs):
        try:
            analyzed, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        except Exception:
            return None
        if analyzed is None or len(analyzed) == 0 or "low10" not in analyzed:
            return None
        level = self._stop_level(analyzed, trade.open_date_utc, trade.open_rate, current_time)
        if level is None or not current_rate or current_rate <= 0:
            return None
        distance = 1.0 - level / current_rate
        # a level at or above the price: stop as tight as possible so the engine exits
        return max(distance, 0.0001)

    @staticmethod
    def _stop_level(dataframe: DataFrame, open_date, entry_price: float, current_time):
        """Stop level S from closed bars only: signal bar t .. last bar closed at current_time."""
        dates = pd.to_datetime(dataframe["date"], utc=True)
        signal_date = pd.Timestamp(open_date).floor("15min") - BAR
        last_closed = pd.Timestamp(current_time) - BAR
        window = dataframe.loc[(dates >= signal_date) & (dates <= last_closed), "low10"]
        if len(window) == 0 or dates[window.index[0]] != signal_date:
            return None
        lows = window.astype(float)
        if lows.isna().any():
            return None
        level = min(float(lows.iloc[0]), (1.0 - MIN_INITIAL_STOP_PCT) * entry_price)
        if len(lows) > 1:
            level = max(level, float(lows.iloc[1:].max()))
        return level

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_time - trade.open_date_utc >= TIME_EXIT_BARS * BAR:
            return "time_exit_8h"
        if current_profit >= TAKE_PROFIT_PCT:
            return "take_profit_2pct"
        return None
