"""H-068: time-of-day-adjusted volume surprise on a strong 1h up bar, 12-hour continuation hold.

Closed 1h candles only, UTC clock; signal at the close of bar t, fill at the open of bar t+1.
Spot long only, one position per pair, no filters beyond the rule.

Definitions (completed bars only):
  Vexp(t) = mean of volume at bars t-24, t-48, ..., t-480 (same UTC hour, 20 previous days);
            any of the 20 values missing or Vexp(t) == 0 -> no signal
  VS(t)   = volume(t) / Vexp(t)
  B(t)    = close(t)/open(t) - 1
  CL(t)   = (close(t) - low(t)) / (high(t) - low(t)); high == low -> no signal
Entry at the close of bar t when all hold:
  (1) VS(t) >= 2.0, (2) B(t) >= 0.006, (3) CL(t) >= 0.7, (4) no open position (engine).
LOWSIG = low(t) is stored in the entry tag, fixed for the trade.
Exits (signal at a bar close, fill at the next bar open), first of:
  (a) time exit at the close of bar t+12, filled at the open of bar t+13
      (= entry fill time + 12 bars)
  (b) close(u) < LOWSIG for a closed bar u >= t+1 (the entry-fill bar is the first checked)
  (c) native intrabar stop 2% below entry (stoploss = -0.02).
No take-profit, no trailing, no cooldown. Warm-up 500 bars.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR = timedelta(hours=1)
SAME_HOUR_LAG_BARS = 24
VOLUME_REFERENCE_DAYS = 20
VOLUME_SURPRISE_MIN = 2.0
BAR_RETURN_MIN = 0.006
CLOSE_LOCATION_MIN = 0.7
HOLD_BARS = 12
TAG_PREFIX = "svs1h"


def make_tag(low_sig: float) -> str:
    return f"{TAG_PREFIX}|{low_sig!r}"


def parse_tag(tag):
    """LOWSIG recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        return float(parts[1])
    except ValueError:
        return None


class SeasonalVolumeSurprise_H068_v1(IStrategy):
    """Buy a strong 1h up bar on twice the same-hour volume norm; hold 12 bars."""

    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.02
    trailing_stop = False
    startup_candle_count = 500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        open_ = dataframe["open"].astype(float)
        high = dataframe["high"].astype(float)
        low = dataframe["low"].astype(float)
        close = dataframe["close"].astype(float)
        volume = dataframe["volume"].astype(float)

        # Sum of volume at t-24k, k = 1..20; NaN if any of the 20 is missing.
        total = None
        for k in range(1, VOLUME_REFERENCE_DAYS + 1):
            lagged = volume.shift(SAME_HOUR_LAG_BARS * k)
            total = lagged if total is None else total + lagged
        vexp = total / float(VOLUME_REFERENCE_DAYS)
        dataframe["vexp"] = vexp
        dataframe["vol_surprise"] = (volume / vexp.where(vexp != 0)).replace([np.inf, -np.inf], np.nan)
        dataframe["bar_ret"] = close / open_ - 1.0
        rng = high - low
        dataframe["close_loc"] = (close - low) / rng.where(rng != 0)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vs = dataframe["vol_surprise"]
        bar_ret = dataframe["bar_ret"]
        close_loc = dataframe["close_loc"]
        cond = (
            dataframe["vexp"].notna()
            & (dataframe["vexp"] != 0)
            & vs.notna()
            & bar_ret.notna()
            & close_loc.notna()
            & dataframe["low"].notna()
            & dataframe["volume"].notna()
            & (dataframe["high"] != dataframe["low"])
            & (vs >= VOLUME_SURPRISE_MIN)
            & (bar_ret >= BAR_RETURN_MIN)
            & (close_loc >= CLOSE_LOCATION_MIN)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(float(lo)) for lo in dataframe.loc[cond, "low"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Both exits depend on per-trade state (LOWSIG, entry time); handled in custom_exit.
        return dataframe

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        low_sig = parse_tag(trade.enter_tag)
        if low_sig is not None:
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
                        and close < low_sig
                    ):
                        return "close_below_signal_low"
        # Close of bar t+12 = entry fill time (open of t+1) + 12 bars.
        if current_time >= trade.open_date_utc + BAR * HOLD_BARS:
            return "time_exit_12_bars"
        return None
