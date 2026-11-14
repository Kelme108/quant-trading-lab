"""H-136: Parabolic SAR up-flip on a 1.5x volume surge, 15m, Wilder SAR trail, 12h cap.

Rule (research/proposals/H-136.json), 15m, UTC, closed bars only, spot, long only:
- PSAR (Wilder, causal loop): AF start 0.02, step 0.02, max 0.20. Bar 0: dir=up, SAR=low, EP=high,
  AF=0.02, NXT(0)=SAR(0). For t>=1, S=NXT(t-1): up and low<S -> flip down (SAR=EP, EP=low, AF=0.02);
  down and high>S -> flip up (SAR=EP, EP=high, AF=0.02); else SAR=S and a new extreme moves EP and
  AF=min(AF+0.02, 0.20). NXT(t)=SAR+AF*(EP-SAR), capped at min(low(t), low(t-1)) if up and floored
  at max(high(t), high(t-1)) if down. NXT(t) is the SAR of bar t+1, known at the close of t.
- ENTRY at the close of t: dir(t-1)=down, dir(t)=up, volume(t)>=1.5 x mean volume of bars t-20..t-1,
  close(t)>open(t). NXT(t) travels in enter_tag ("psar:<nxt>").
- FILL CHECK (confirm_trade_entry, rate E): skip if NXT(t) < 0.97 x E.
- INITIAL STOP frozen at the fill: S0 = min(NXT(t), 0.99 x E), G = NXT(t) - S0.
- TRAIL (custom_stoploss): for bar k, L(k) = max(S0, NXT(k-1) - G), NXT(k-1) read from the last closed
  candle. Native stoploss -0.03 is only a backstop.
- SAR EXIT: exit signal when dir(k)=down at the close of k (sold at the next open).
- TIME EXIT: 12 h (48 bars) after the fill, in custom_exit. No take-profit, cooldown or other filter.
- Warm-up 500 bars.
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

AF_START = 0.02
AF_STEP = 0.02
AF_MAX = 0.20
VOLUME_MEAN_BARS = 20
VOLUME_MULT = 1.5
MIN_INITIAL_STOP_PCT = 0.01
MAX_SAR_DISTANCE_PCT = 0.03
TIME_EXIT_HOURS = 12  # 48 bars of 15m
BAR = timedelta(minutes=15)
TAG_PREFIX = "psar:"


def parse_tag(tag):
    if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
        return None
    try:
        value = float(tag[len(TAG_PREFIX):])
    except ValueError:
        return None
    return value if np.isfinite(value) and value > 0 else None


def wilder_sar(high: np.ndarray, low: np.ndarray):
    """Causal Wilder SAR. Returns (direction +1/-1/NaN, sar, nxt) arrays."""
    n = len(high)
    direction = np.full(n, np.nan)
    sar = np.full(n, np.nan)
    nxt = np.full(n, np.nan)
    started = False
    up = True
    ep = af = cur_sar = prev_nxt = np.nan
    prev_high = prev_low = np.nan
    for t in range(n):
        h = high[t]
        lo = low[t]
        if not (np.isfinite(h) and np.isfinite(lo)):
            continue  # undefined bar: no output, state carried
        if not started:
            started = True
            up = True
            cur_sar = lo
            ep = h
            af = AF_START
            direction[t] = 1.0
            sar[t] = cur_sar
            nxt[t] = cur_sar
            prev_nxt = cur_sar
            prev_high, prev_low = h, lo
            continue
        s = prev_nxt
        if up and lo < s:
            up = False
            cur_sar = ep
            ep = lo
            af = AF_START
        elif (not up) and h > s:
            up = True
            cur_sar = ep
            ep = h
            af = AF_START
        else:
            cur_sar = s
            if up and h > ep:
                ep = h
                af = min(af + AF_STEP, AF_MAX)
            elif (not up) and lo < ep:
                ep = lo
                af = min(af + AF_STEP, AF_MAX)
        candidate = cur_sar + af * (ep - cur_sar)
        if up:
            candidate = min(candidate, lo, prev_low)
        else:
            candidate = max(candidate, h, prev_high)
        direction[t] = 1.0 if up else -1.0
        sar[t] = cur_sar
        nxt[t] = candidate
        prev_nxt = candidate
        prev_high, prev_low = h, lo
    return direction, sar, nxt


class ParabolicSARVolumeFlip_H136_v1(IStrategy):
    """Wilder SAR up-flip on a volume surge and an up close, SAR-shifted trail, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 500

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        direction, sar, nxt = wilder_sar(
            dataframe["high"].to_numpy(dtype=float), dataframe["low"].to_numpy(dtype=float)
        )
        dataframe["psar_dir"] = direction
        dataframe["psar"] = sar
        dataframe["psar_nxt"] = nxt
        # mean volume of the previous 20 bars; the current bar is excluded
        dataframe["vmean"] = dataframe["volume"].shift(1).rolling(VOLUME_MEAN_BARS).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        prev_dir = dataframe["psar_dir"].shift(1)
        ok = (
            prev_dir.notna()
            & dataframe["psar_dir"].notna()
            & dataframe["psar_nxt"].notna()
            & dataframe["vmean"].notna()
            & (prev_dir == -1)
            & (dataframe["psar_dir"] == 1)
            & (dataframe["volume"] > 0)
            & (dataframe["volume"] >= VOLUME_MULT * dataframe["vmean"])
            & (dataframe["close"] > dataframe["open"])
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            dataframe.loc[ok, "enter_tag"] = dataframe.loc[ok, "psar_nxt"].map(
                lambda value: TAG_PREFIX + repr(float(value))
            )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["psar_dir"].notna()
            & (dataframe["psar_dir"] == -1)
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "exit_long"] = 1
            dataframe.loc[ok, "exit_tag"] = "sar_down"
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        nxt = parse_tag(entry_tag)
        if nxt is None or not rate or rate <= 0:
            return False
        if nxt < (1.0 - MAX_SAR_DISTANCE_PCT) * rate:
            return False
        return True

    def _last_closed_nxt(self, pair, current_time):
        try:
            dp = self.dp
        except AttributeError:
            return None
        if dp is None:
            return None
        dataframe, _ = dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or len(dataframe) == 0 or "psar_nxt" not in dataframe:
            return None
        closed = dataframe[pd.to_datetime(dataframe["date"]) + BAR <= current_time]
        if len(closed) == 0:
            return None
        value = closed["psar_nxt"].iloc[-1]
        return float(value) if np.isfinite(value) else None

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        nxt_t = parse_tag(trade.enter_tag)
        entry = trade.open_rate
        if nxt_t is None or not entry or not current_rate:
            return None  # fall back to the native backstop
        s0 = min(nxt_t, (1.0 - MIN_INITIAL_STOP_PCT) * entry)
        gap = nxt_t - s0
        level = s0
        nxt_prev = self._last_closed_nxt(pair, current_time)
        if nxt_prev is not None:
            level = max(s0, nxt_prev - gap)
        ratio = level / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the stop level: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
