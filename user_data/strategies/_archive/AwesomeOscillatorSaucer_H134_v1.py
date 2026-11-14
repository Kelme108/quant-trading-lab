"""H-134: Awesome Oscillator saucer on 15m (research/proposals/H-134.json).

Rule, 15m, closed bars only, long only, spot. Signal at the close of bar t, fill at the
open of bar t+1 (E):
- mp = (high+low)/2; AO = SMA(mp,5) - SMA(mp,34); ATR14 = Wilder ATR (alpha 1/14).
- LL6(t) = lowest low of bars t-5..t.
- SAUCER(t): AO(t-3..t) all > 0, AO(t-2)<AO(t-3), AO(t-1)<AO(t-2), AO(t)>AO(t-1).
- ENTRY: SAUCER, ATR14/close >= 0.004, close > open, and a usable stop distance:
  raw = (close - LL6)/close; raw > 0.025 -> skip; else d = max(raw, 0.01).
- STOP: E x (1 - d) (custom_stoploss, d fixed at the signal; `stoploss` = -0.025 is the
  widest possible d and the fallback).
- TAKE-PROFIT: E x (1 + 1.5 d), in custom_exit.
- SIGNAL EXIT: a bar closes with AO < 0 -> exit at the next open (exit_long).
- TIME EXIT: 48 bars (12 hours) after the entry, in custom_exit.
- No cooldown, no daily limits, no pyramiding. Warm-up 400 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

AO_FAST = 5
AO_SLOW = 34
ATR_PERIOD = 14
ATR_MIN_PCT = 0.004
SWING_LOW_BARS = 6
MIN_STOP_PCT = 0.01
MAX_STOP_PCT_SKIP = 0.025
TARGET_R = 1.5
TIME_EXIT_BARS = 48
BAR_MINUTES = 15


class AwesomeOscillatorSaucer_H134_v1(IStrategy):
    """AO saucer above zero + ATR activity filter + green bar, per-trade stop 1%-2.5%, 1.5R target."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.025
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        mp = (dataframe["high"] + dataframe["low"]) / 2.0
        ao = mp.rolling(AO_FAST).mean() - mp.rolling(AO_SLOW).mean()
        dataframe["ao"] = ao
        dataframe["ao_1"] = ao.shift(1)
        dataframe["ao_2"] = ao.shift(2)
        dataframe["ao_3"] = ao.shift(3)

        prev_close = dataframe["close"].shift(1)
        true_range = pd.concat(
            [
                dataframe["high"] - dataframe["low"],
                (dataframe["high"] - prev_close).abs(),
                (dataframe["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        dataframe["atr"] = true_range.ewm(alpha=1.0 / ATR_PERIOD, adjust=False).mean()
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        ll = dataframe["low"].rolling(SWING_LOW_BARS).min()
        raw = (dataframe["close"] - ll) / dataframe["close"]
        stop_dist = raw.clip(lower=MIN_STOP_PCT)
        dataframe["stop_dist"] = stop_dist.where(raw <= MAX_STOP_PCT_SKIP)
        return dataframe

    def _defined(self, dataframe: DataFrame) -> pd.Series:
        cols = ["ao", "ao_1", "ao_2", "ao_3", "atr_pct"]
        return dataframe[cols].notna().all(axis=1) & (dataframe["volume"] > 0)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        saucer = (
            (dataframe["ao_3"] > 0)
            & (dataframe["ao_2"] > 0)
            & (dataframe["ao_1"] > 0)
            & (dataframe["ao"] > 0)
            & (dataframe["ao_2"] < dataframe["ao_3"])
            & (dataframe["ao_1"] < dataframe["ao_2"])
            & (dataframe["ao"] > dataframe["ao_1"])
        )
        active = dataframe["atr_pct"] >= ATR_MIN_PCT
        green = dataframe["close"] > dataframe["open"]
        stop_ok = dataframe["stop_dist"].notna()
        signal = self._defined(dataframe) & saucer & active & green & stop_ok
        dataframe.loc[signal, ["enter_long", "enter_tag"]] = (1, "ao_saucer")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        signal = self._defined(dataframe) & (dataframe["ao"] < 0)
        dataframe.loc[signal, ["exit_long", "exit_tag"]] = (1, "ao_below_zero")
        return dataframe

    def _trade_stop_distance(self, pair: str, trade):
        """Stop distance d fixed at the signal bar (the closed bar before the fill bar)."""
        analyzed, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if analyzed is None or len(analyzed) == 0 or "stop_dist" not in analyzed:
            return None
        fill_bar = pd.Timestamp(trade.open_date_utc).floor(f"{BAR_MINUTES}min")
        signal_bar = fill_bar - timedelta(minutes=BAR_MINUTES)
        rows = analyzed.loc[pd.to_datetime(analyzed["date"], utc=True) == signal_bar, "stop_dist"]
        if len(rows) == 0:
            return None
        value = rows.iloc[-1]
        if value is None or not np.isfinite(value) or value <= 0:
            return None
        return float(value)

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs
    ):
        d = self._trade_stop_distance(pair, trade)
        if d is None or current_rate <= 0:
            return None
        stop_price = trade.open_rate * (1.0 - d)
        return stop_price / current_rate - 1.0

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        d = self._trade_stop_distance(pair, trade)
        if d is not None and current_profit >= TARGET_R * d:
            return "take_profit_1_5R"
        if current_time - trade.open_date_utc >= timedelta(minutes=BAR_MINUTES * TIME_EXIT_BARS):
            return "time_exit_12h"
        return None
