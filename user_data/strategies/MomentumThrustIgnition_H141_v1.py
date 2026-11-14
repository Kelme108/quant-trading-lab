"""H-141: 1h momentum thrust from rest (RSI <=50 to >=70 within 3 bars) on a 2x range, 2x volume bar.

Rule (research/proposals/H-141.json), 1h, UTC, closed bars only, spot, long only:
- RSI14 = Wilder RSI(14) of closes (talib). MR(t) = mean(high-low) of bars t-20..t-1,
  MV(t) = mean volume of bars t-20..t-1 (bar t excluded).
- IGNITION at bar t: RSI14(t) >= 70; min(RSI14(t-3..t-1)) <= 50; range(t) >= 2.0 x MR(t);
  high > low and (close-low)/(high-low) >= 0.75; volume(t) >= 2.0 x MV(t).
- ENTRY: buy at the open of t+1 (signal at the close of t). low(t) and high(t) travel in the
  enter_tag ("mti:<low>:<high>"); the midpoint M = (high+low)/2.
- STOP (intrabar, frozen): stop_pct = max((entry - low(t)) / entry, 0.01), capped at 10%;
  stop price = entry x (1 - stop_pct). Implemented in custom_stoploss as a fixed absolute
  price; the native stoploss -0.10 is only a backstop.
- EXITS in custom_exit (closed candles only), after the stop:
  TARGET T = entry + 2 x (entry - stop price): the engine cannot fill a per-trade price
  intrabar, so the stated fallback is used: exit at the close of the first closed 1h bar
  whose close >= T (the order fills at the next open).
  FAIL-FAST: a closed bar (from the entry bar on) with close < M.
  TIME: sell at the open of bar t+13, i.e. 12 hours after the entry bar opened.
- No cooldown. Warm-up 400 bars (the proposal says 300; the repo's recursive-indicator check
  requires at least 400; more history loaded before trading does not change the rule).
"""

from datetime import timedelta

import numpy as np
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy

RSI_LENGTH = 14
RSI_THRUST = 70.0
RSI_REST = 50.0
REST_BARS = 3
LOOKBACK = 20
RANGE_MULT = 2.0
CLOSE_LOC_MIN = 0.75
VOLUME_MULT = 2.0
MIN_STOP_PCT = 0.01
MAX_STOP_PCT = 0.10
TARGET_R = 2.0
TIME_EXIT_HOURS = 12
TAG_PREFIX = "mti:"


class MomentumThrustIgnition_H141_v1(IStrategy):
    """RSI neutral-to-overbought thrust on an oversized, high-volume, strong-close 1h bar."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400  # proposal: 300; repo check needs >= 400 for recursive RSI
    dp = None  # set by Freqtrade; None keeps the time exit usable without a data provider

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=RSI_LENGTH)
        # lowest RSI of the three bars before the current one
        dataframe["rsi_rest_min"] = dataframe["rsi14"].shift(1).rolling(REST_BARS).min()

        bar_range = dataframe["high"] - dataframe["low"]
        dataframe["bar_range"] = bar_range
        # means over bars t-20..t-1: the current bar is excluded
        dataframe["mean_range"] = bar_range.shift(1).rolling(LOOKBACK).mean()
        dataframe["mean_volume"] = dataframe["volume"].shift(1).rolling(LOOKBACK).mean()

        valid_range = bar_range > 0
        dataframe["close_loc"] = (
            (dataframe["close"] - dataframe["low"]).where(valid_range) / bar_range.where(valid_range)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        defined = (
            dataframe["rsi14"].notna()
            & dataframe["rsi_rest_min"].notna()
            & dataframe["mean_range"].notna()
            & dataframe["mean_volume"].notna()
            & dataframe["close_loc"].notna()
        )
        ignition = (
            defined
            & (dataframe["volume"] > 0)
            & (dataframe["rsi14"] >= RSI_THRUST)
            & (dataframe["rsi_rest_min"] <= RSI_REST)
            & (dataframe["bar_range"] >= RANGE_MULT * dataframe["mean_range"])
            & (dataframe["high"] > dataframe["low"])
            & (dataframe["close_loc"] >= CLOSE_LOC_MIN)
            & (dataframe["volume"] >= VOLUME_MULT * dataframe["mean_volume"])
        )
        if ignition.any():
            dataframe.loc[ignition, "enter_long"] = 1
            tags = [
                TAG_PREFIX + repr(float(low)) + ":" + repr(float(high))
                for low, high in zip(
                    dataframe.loc[ignition, "low"], dataframe.loc[ignition, "high"]
                )
            ]
            dataframe.loc[ignition, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: stop, target, fail-fast and time exit are trade-specific.
        return dataframe

    @staticmethod
    def _signal_bar(trade):
        """(low, high) of the ignition bar from the entry tag, or None."""
        tag = trade.enter_tag
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        parts = tag[len(TAG_PREFIX):].split(":")
        if len(parts) != 2:
            return None
        try:
            low = float(parts[0])
            high = float(parts[1])
        except ValueError:
            return None
        if not (np.isfinite(low) and np.isfinite(high)) or low <= 0 or high < low:
            return None
        return low, high

    @staticmethod
    def _stop_pct(entry: float, low: float) -> float:
        return min(max((entry - low) / entry, MIN_STOP_PCT), MAX_STOP_PCT)

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        bar = self._signal_bar(trade)
        entry = trade.open_rate
        if bar is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        stop_price = entry * (1.0 - self._stop_pct(entry, bar[0]))
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        step = timedelta(hours=1)
        entry_bar = trade.open_date_utc.replace(minute=0, second=0, microsecond=0)

        bar = self._signal_bar(trade)
        entry = trade.open_rate
        dp = self.dp
        if bar is not None and entry and dp is not None:
            dataframe, _ = dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[
                    (dataframe["date"] + step <= current_time) & (dataframe["date"] >= entry_bar)
                ]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    if last["volume"] > 0 and last["close"] == last["close"]:
                        stop_pct = self._stop_pct(entry, bar[0])
                        target = entry * (1.0 + TARGET_R * stop_pct)
                        if last["close"] >= target:
                            return "target_2r"
                        midpoint = (bar[0] + bar[1]) / 2.0
                        if last["close"] < midpoint:
                            return "fail_fast_midpoint"

        if current_time - entry_bar >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
