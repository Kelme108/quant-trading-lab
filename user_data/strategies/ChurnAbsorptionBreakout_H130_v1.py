"""H-130: 15m churn absorption after a decline, buy the wide-bar close above the zone.

Rule (research/proposals/H-130.json), 15m, closed bars only, spot, long only:
- MV(t) / MR(t): mean volume / mean (high-low) of bars t-96..t-1 (bar t excluded).
- CHURN bar c: volume >= 2.0 x MV and (high-low) <= 0.6 x MR.
- CONTEXT: close(c-32) - close(c) >= 3.0 x MR(c).
- ZONE START: a churn bar with CONTEXT that is not an extension of a live zone opens a zone
  (ZH = high, ZL = low, end z = c) and replaces any older unused zone.
- EXTENSION: a churn bar c' with 1 <= c'-z <= 4 (CONTEXT not needed) widens the zone, z = c'.
- VOID: a bar after the start that closes below ZL cancels the zone (checked against the zone
  as it stood before that bar, so a churn bar closing below ZL voids instead of extending);
  no entry by bar z+16 cancels it too.
- ENTRY: the first bar t with 1 <= t-z <= 16, close > ZH and (high-low) >= 1.5 x MR is the
  breakout bar; the zone is used up at that bar. If ZL < 0.97 x close(t) there is no trade,
  otherwise the entry signal is raised and the order fills at the next open (price E).
  A position already open on the pair simply ignores the signal (one position per pair).
- STOP: S = min(ZL, 0.99 x E), i.e. d = max(1%, (E-ZL)/E), fixed at entry (custom_stoploss,
  from the zone low carried in enter_tag "cab:<ZL>"); native stoploss -5% is only a backstop.
- TARGET: T = E + 1.5 x (E-S), i.e. profit >= 1.5 x d (custom_exit).
- TIME EXIT: 12 h after the fill (48 bars) in custom_exit.
- Warm-up 200 bars. Bars are counted by row.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BASELINE_BARS = 96
CHURN_VOLUME_MULT = 2.0
CHURN_RANGE_MAX_MULT = 0.6
CONTEXT_BARS = 32
CONTEXT_DECLINE_MR_MULT = 3.0
ZONE_EXTENSION_BARS = 4
ENTRY_WINDOW_BARS = 16
BREAKOUT_RANGE_MIN_MULT = 1.5
MAX_ZONE_DEPTH = 0.97
MIN_STOP_PCT = 0.01
TARGET_R_MULTIPLE = 1.5
TIME_EXIT_HOURS = 12  # 48 bars of 15m
TAG_PREFIX = "cab:"


class ChurnAbsorptionBreakout_H130_v1(IStrategy):
    """Volume-heavy narrow-range zone after a decline; buy the wide-bar close above it, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.05
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        bar_range = dataframe["high"] - dataframe["low"]
        # baselines over the previous 96 bars; the current bar is excluded
        dataframe["cab_mv"] = dataframe["volume"].shift(1).rolling(BASELINE_BARS).mean()
        dataframe["cab_mr"] = bar_range.shift(1).rolling(BASELINE_BARS).mean()

        churn = (
            dataframe["cab_mv"].notna()
            & dataframe["cab_mr"].notna()
            & (dataframe["volume"] >= CHURN_VOLUME_MULT * dataframe["cab_mv"])
            & (bar_range <= CHURN_RANGE_MAX_MULT * dataframe["cab_mr"])
        )
        context = (
            dataframe["cab_mr"].notna()
            & ((dataframe["close"].shift(CONTEXT_BARS) - dataframe["close"])
               >= CONTEXT_DECLINE_MR_MULT * dataframe["cab_mr"])
        )
        dataframe["cab_churn"] = churn
        dataframe["cab_context"] = context

        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        volume = dataframe["volume"].to_numpy(dtype=float)
        mr = dataframe["cab_mr"].to_numpy(dtype=float)
        rng = bar_range.to_numpy(dtype=float)
        is_churn = churn.to_numpy(dtype=bool)
        has_context = context.to_numpy(dtype=bool)

        signal = np.zeros(n, dtype=bool)
        signal_zl = np.full(n, np.nan)
        live = False
        zh = zl = np.nan
        z = 0
        for i in range(n):
            if live:
                if close[i] < zl:  # closed below the zone low: void
                    live = False
                elif i - z > ENTRY_WINDOW_BARS:  # no entry by bar z+16: void
                    live = False
            if live:
                gap = i - z
                if is_churn[i] and 1 <= gap <= ZONE_EXTENSION_BARS:
                    zh = max(zh, high[i])
                    zl = min(zl, low[i])
                    z = i
                    continue
                if (
                    1 <= gap <= ENTRY_WINDOW_BARS
                    and np.isfinite(mr[i])
                    and close[i] > zh
                    and rng[i] >= BREAKOUT_RANGE_MIN_MULT * mr[i]
                ):
                    live = False  # the zone is used up at its breakout bar
                    if zl >= MAX_ZONE_DEPTH * close[i] and volume[i] > 0:
                        signal[i] = True
                        signal_zl[i] = zl
                    continue
            if is_churn[i] and has_context[i]:
                live = True
                zh = high[i]
                zl = low[i]
                z = i

        dataframe["cab_signal"] = signal
        dataframe["cab_zl"] = signal_zl
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["cab_signal"].fillna(False).astype(bool)
            & dataframe["cab_zl"].notna()
            & dataframe["cab_mv"].notna()
            & dataframe["cab_mr"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "cab_zl"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the target and the time exit.
        return dataframe

    @staticmethod
    def _zone_low(trade):
        tag = trade.enter_tag
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        try:
            value = float(tag[len(TAG_PREFIX):])
        except ValueError:
            return None
        return value if np.isfinite(value) and value > 0 else None

    @staticmethod
    def _stop_distance(entry: float, zone_low: float) -> float:
        return max(MIN_STOP_PCT, (entry - zone_low) / entry)

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        zone_low = self._zone_low(trade)
        entry = trade.open_rate
        if zone_low is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        stop_price = entry * (1.0 - self._stop_distance(entry, zone_low))
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        zone_low = self._zone_low(trade)
        entry = trade.open_rate
        if zone_low is not None and entry:
            target = TARGET_R_MULTIPLE * self._stop_distance(entry, zone_low)
            if current_profit >= target:
                return "target_1_5r"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
