"""H-137: US 08:30 New York macro-release spike, buy the first close above the release-bar high (15m).

Rule (research/proposals/H-137.json), 15m, closed bars only, spot, long only:
- CLOCK: UTC bar open time converted to America/New_York (DST aware). Weekdays only.
- RELEASE BAR E: the 15m bar whose NY open time is 08:30 on a weekday.
- BASELINE(E): median of (high - low) of the 08:30 NY bars of the 20 most recent EARLIER weekdays
  present in the data within the 2900 bars before E (E excluded). Fewer than 20 -> no event.
- EVENT: range(E) >= 3.0 x BASELINE(E) and range(E) / open(E) >= 0.008.
- ENTRY WINDOW: the 8 bars after E (NY 08:45..10:30). Signal at the close of the FIRST bar t of the
  window with close(t) > high(E); only that bar counts. Fill at the next open (price P).
  low(E) travels in enter_tag ("mrr:<low>").
- STOP: d = max(1 - low(E)/P, 0.01), frozen at the fill; stop price P x (1 - d), custom_stoploss;
  native stoploss -0.20 is only a backstop.
- TARGET: T = P x (1 + 1.5 d) in custom_exit. TIME EXIT: 8h after the fill (bar e+32 open) in custom_exit.
- Warm-up 3000 bars. No other filters or exits.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR_MINUTES = 15
NY_TZ = "America/New_York"
RELEASE_HOUR = 8
RELEASE_MINUTE = 30
BASELINE_DAYS = 20
BASELINE_SEARCH_BARS = 2900
RANGE_VS_BASELINE_MIN = 3.0
RANGE_OVER_OPEN_MIN = 0.008
ENTRY_WINDOW_BARS = 8
STOP_FLOOR_PCT = 0.01
TARGET_R_MULTIPLE = 1.5
TIME_EXIT_HOURS = 8  # 32 bars of 15m
TAG_PREFIX = "mrr:"


class MacroReleaseResolution_H137_v1(IStrategy):
    """First 15m close above a violent 08:30 NY release bar's high, 1.5R target or 8h."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.20
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 3000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        signal = np.zeros(n, dtype=bool)
        signal_low = np.full(n, np.nan)

        if n:
            utc = pd.to_datetime(dataframe["date"], utc=True)
            local = utc.dt.tz_convert(NY_TZ)
            is_release = (
                (local.dt.hour == RELEASE_HOUR)
                & (local.dt.minute == RELEASE_MINUTE)
                & (local.dt.day_of_week < 5)
            ).to_numpy()
            times = utc.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[ns]").astype("int64")
            bar_ns = BAR_MINUTES * 60 * 1_000_000_000
            high = dataframe["high"].to_numpy(dtype=float)
            low = dataframe["low"].to_numpy(dtype=float)
            open_ = dataframe["open"].to_numpy(dtype=float)
            close = dataframe["close"].to_numpy(dtype=float)
            bar_range = high - low

            rel_idx = np.flatnonzero(is_release)
            rel_times = times[rel_idx]
            rel_range = bar_range[rel_idx]

            for k, i in enumerate(rel_idx):
                if not (np.isfinite(bar_range[i]) and np.isfinite(open_[i]) and open_[i] > 0):
                    continue
                # earlier release bars within the 2900 bars before E
                earlier = [
                    j for j in range(max(0, k - 40), k)
                    if rel_times[k] - rel_times[j] <= BASELINE_SEARCH_BARS * bar_ns
                    and np.isfinite(rel_range[j])
                ]
                if len(earlier) < BASELINE_DAYS:
                    continue
                baseline = float(np.median(rel_range[earlier[-BASELINE_DAYS:]]))
                if not np.isfinite(baseline) or baseline <= 0:
                    continue
                if bar_range[i] < RANGE_VS_BASELINE_MIN * baseline:
                    continue
                if bar_range[i] / open_[i] < RANGE_OVER_OPEN_MIN:
                    continue
                # entry window: bars strictly after E up to 8 bars (time based)
                end_time = times[i] + ENTRY_WINDOW_BARS * bar_ns
                j = i + 1
                while j < n and times[j] <= end_time:
                    if np.isfinite(close[j]) and close[j] > high[i]:
                        signal[j] = True
                        signal_low[j] = low[i]
                        break
                    j += 1

        dataframe["mrr_signal"] = signal
        dataframe["mrr_low"] = signal_low
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["mrr_signal"].fillna(False).astype(bool)
            & dataframe["mrr_low"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "mrr_low"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the target and the time exit.
        return dataframe

    @staticmethod
    def _release_low(trade):
        tag = trade.enter_tag
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        try:
            value = float(tag[len(TAG_PREFIX):])
        except ValueError:
            return None
        return value if np.isfinite(value) and value > 0 else None

    @staticmethod
    def _distance(release_low: float, entry: float) -> float:
        return max(1.0 - release_low / entry, STOP_FLOOR_PCT)

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        release_low = self._release_low(trade)
        entry = trade.open_rate
        if release_low is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        stop_price = entry * (1.0 - self._distance(release_low, entry))
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        release_low = self._release_low(trade)
        entry = trade.open_rate
        if release_low is not None and entry and current_rate:
            target = entry * (1.0 + TARGET_R_MULTIPLE * self._distance(release_low, entry))
            if current_rate >= target:
                return "target_1_5R"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_8h"
        return None
