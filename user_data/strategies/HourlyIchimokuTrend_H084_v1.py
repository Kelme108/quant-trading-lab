"""H-084: Hourly Ichimoku 20/60/120/30 trend entry with Kijun exit, 3% stop and 24h cap.

Chart 1h, closed candles only; signals at the close of bar t fill at the open of bar t+1.
All windows include the current closed bar t (as the rule states):
- Tenkan T(t)  = (max high + min low of bars t-19..t) / 2
- Kijun K(t)   = (max high + min low of bars t-59..t) / 2
- SpanA_raw(t) = (T(t) + K(t)) / 2
- SpanB_raw(t) = (max high + min low of bars t-119..t) / 2
- Cloud at bar t uses values displaced by 30 bars: SpanA(t) = SpanA_raw(t-30), SpanB(t) = SpanB_raw(t-30),
  CloudTop(t) = max(SpanA(t), SpanB(t)).

Entry (flat): close(t) > CloudTop(t) and close(t) > close(t-30) and at least one of
  (A) TK cross: T(t-1) <= K(t-1) and T(t) > K(t)
  (B) cloud break: close(t-1) <= CloudTop(t-1) and T(t) > K(t).
Exits, first of: native 3% stop (intrabar); close(t) < K(t) (exit signal, next open);
time exit 24 hours after entry (close of the 24th bar counting the entry bar as bar 1, i.e. open of bar 25).
No take-profit, trailing stop, cooldown or pyramiding.
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy

TENKAN_PERIOD = 20
KIJUN_PERIOD = 60
SPANB_PERIOD = 120
DISPLACEMENT = 30
LAGGING_LOOKBACK = 30
MAX_HOLD_BARS = 24


def range_midpoint(dataframe: DataFrame, period: int):
    """Midpoint of the high/low range over the last `period` bars, current bar included (backward-only)."""
    return (dataframe["high"].rolling(period).max() + dataframe["low"].rolling(period).min()) / 2.0


class HourlyIchimokuTrend_H084_v1(IStrategy):
    """Ichimoku TK cross / cloud break above the displaced cloud, Kijun exit, 24h cap."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    use_custom_stoploss = False
    use_exit_signal = True
    process_only_new_candles = True
    # 120-bar SpanB plus 30-bar displacement (the rule's 150-bar warm-up).
    startup_candle_count = 150

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["tenkan"] = range_midpoint(dataframe, TENKAN_PERIOD)
        dataframe["kijun"] = range_midpoint(dataframe, KIJUN_PERIOD)
        span_a_raw = (dataframe["tenkan"] + dataframe["kijun"]) / 2.0
        span_b_raw = range_midpoint(dataframe, SPANB_PERIOD)
        dataframe["span_a"] = span_a_raw.shift(DISPLACEMENT)
        dataframe["span_b"] = span_b_raw.shift(DISPLACEMENT)
        # np.maximum propagates NaN, so the cloud top is undefined until both spans are defined.
        dataframe["cloud_top"] = np.maximum(dataframe["span_a"], dataframe["span_b"])
        dataframe["close_lag"] = dataframe["close"].shift(LAGGING_LOOKBACK)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tenkan = dataframe["tenkan"]
        kijun = dataframe["kijun"]
        cloud_top = dataframe["cloud_top"]
        close = dataframe["close"]
        tenkan_prev = tenkan.shift(1)
        kijun_prev = kijun.shift(1)
        cloud_top_prev = cloud_top.shift(1)
        close_prev = close.shift(1)

        ready = (
            tenkan.notna()
            & kijun.notna()
            & tenkan_prev.notna()
            & kijun_prev.notna()
            & cloud_top.notna()
            & cloud_top_prev.notna()
            & close_prev.notna()
            & dataframe["close_lag"].notna()
        )
        live = dataframe["volume"] > 0

        above_cloud = close > cloud_top
        lagging_ok = close > dataframe["close_lag"]
        tk_bull = tenkan > kijun
        tk_cross = (tenkan_prev <= kijun_prev) & tk_bull
        cloud_break = (close_prev <= cloud_top_prev) & tk_bull

        entry = ready & live & above_cloud & lagging_ok & (tk_cross | cloud_break)
        dataframe.loc[entry & tk_cross, ["enter_long", "enter_tag"]] = (1, "tk_cross")
        dataframe.loc[entry & ~tk_cross, ["enter_long", "enter_tag"]] = (1, "cloud_break")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_cond = (
            dataframe["kijun"].notna()
            & (dataframe["volume"] > 0)
            & (dataframe["close"] < dataframe["kijun"])
        )
        dataframe.loc[exit_cond, ["exit_long", "exit_tag"]] = (1, "kijun_exit")
        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> Optional[str]:
        # Entry bar is bar 1 (opens at the fill); after the close of bar 24 the trade is sold at the next open.
        if current_time >= trade.open_date_utc + timedelta(hours=MAX_HOLD_BARS):
            return "time_exit_24h"
        return None
