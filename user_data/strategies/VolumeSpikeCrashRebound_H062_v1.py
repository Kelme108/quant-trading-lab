"""H-062: 15m aggressive-selling bar reversal (volume-confirmed 3-sigma red bar).

Closed 15m candles only; signal at the close of bar t, fill at the open of bar t+1.
Spot long only, one position per pair, no filters beyond the rule.

Definitions (completed bars only):
  r(i)     = close(i)/close(i-1) - 1
  sigma(t) = sample std (ddof=1) of r over bars t-672..t-1 (current bar excluded)
  Vmed(t)  = median volume of bars t-96..t-1 (current bar excluded)
  b(t)     = close(t)/open(t) - 1
Entry at the close of bar t when all hold:
  (1) b(t) <= -max(0.008, 3.0 * sigma(t))
  (2) volume(t) >= 3.0 * Vmed(t)
  (3) no open position (engine), (4) cooldown 8 candles after any exit (CooldownPeriod),
  (5) all inputs defined, volume > 0.
TARGET = open(t) and FLOOR = 0.99 * low(t) are stored in the entry tag, fixed for the trade.
Exits (signal at a bar close, fill at the next bar open), first of:
  (a) close(u) >= TARGET for a closed bar u >= t+1 (the entry bar is the first checked)
  (b) close(u) < FLOOR for a closed bar u >= t+1
  (c) time exit at the close of bar t+16, filled at the open of bar t+17
      (= entry fill time + 16 bars).
Native intrabar stop 3% below entry (stoploss = -0.03). Warm-up 700 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
SIGMA_WINDOW_BARS = 672
SIGMA_MULTIPLE = 3.0
MIN_DROP = 0.008
VOLUME_MEDIAN_WINDOW_BARS = 96
VOLUME_MULTIPLE = 3.0
FLOOR_FACTOR = 0.99
TIME_EXIT_BARS = 16
COOLDOWN_BARS = 8
TAG_PREFIX = "vscr15"


def make_tag(target: float, floor: float) -> str:
    return f"{TAG_PREFIX}|{target!r}|{floor!r}"


def parse_tag(tag):
    """(TARGET, FLOOR) recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        return float(parts[1]), float(parts[2])
    except ValueError:
        return None


class VolumeSpikeCrashRebound_H062_v1(IStrategy):
    """Buy the close of a volume-confirmed 3-sigma red 15m bar; exit on full retrace or 4h."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    trailing_stop = False
    startup_candle_count = 700

    @property
    def protections(self):
        return [{"method": "CooldownPeriod", "stop_duration_candles": COOLDOWN_BARS}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        close = dataframe["close"].astype(float)
        open_ = dataframe["open"].astype(float)
        volume = dataframe["volume"].astype(float)
        ret = close / close.shift(1) - 1.0
        # Returns of bars t-672..t-1: rolling window ending at t-1.
        dataframe["sigma"] = ret.rolling(SIGMA_WINDOW_BARS).std(ddof=1).shift(1)
        # Volumes of bars t-96..t-1.
        dataframe["vmed"] = volume.rolling(VOLUME_MEDIAN_WINDOW_BARS).median().shift(1)
        dataframe["bar_ret"] = close / open_ - 1.0
        dataframe["drop_threshold"] = np.maximum(MIN_DROP, SIGMA_MULTIPLE * dataframe["sigma"])
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sigma = dataframe["sigma"]
        vmed = dataframe["vmed"]
        bar_ret = dataframe["bar_ret"]
        cond = (
            sigma.notna()
            & vmed.notna()
            & bar_ret.notna()
            & dataframe["open"].notna()
            & dataframe["low"].notna()
            & dataframe["volume"].notna()
            & (bar_ret <= -dataframe["drop_threshold"])
            & (dataframe["volume"] >= VOLUME_MULTIPLE * vmed)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(float(o), float(FLOOR_FACTOR * lo))
                for o, lo in zip(dataframe.loc[cond, "open"], dataframe.loc[cond, "low"])
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exits depend on per-trade state (TARGET, FLOOR, entry time); handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        levels = parse_tag(trade.enter_tag)
        if levels is not None:
            target, floor = levels
            dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
            if dataframe is not None and len(dataframe) > 0:
                closed = dataframe[dataframe["date"] + BAR <= current_time]
                if len(closed) > 0:
                    last = closed.iloc[-1]
                    close = last["close"]
                    if (
                        last["date"] >= trade.open_date_utc
                        and last["volume"] > 0
                        and close == close
                    ):
                        if close >= target:
                            return "full_retrace"
                        if close < floor:
                            return "breakdown_below_floor"
        # Close of bar t+16 = entry fill time (open of t+1) + 16 bars.
        if current_time >= trade.open_date_utc + BAR * TIME_EXIT_BARS:
            return "time_exit_16_bars"
        return None
