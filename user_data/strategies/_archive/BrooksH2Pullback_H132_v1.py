"""H-132: Al Brooks H2 two-legged pullback, 15m, pullback-low stop, 1.5R target, 12h exit.

Rule (research/proposals/H-132.json), 15m, UTC, closed bars only, spot, long only:
- INDICATORS: EMA20 of close (talib-style: SMA seed, alpha 2/21), ATR14 Wilder (talib-style
  seed), ATRp = ATR14 / close. Both are implemented here with the same recursion as TA-Lib.
- SETUP: bar P with high(P) > max(high of P-24..P-1). A newer setup bar replaces the active one.
- H1: first bar i >= P+2 with high(i) > high(i-1) and high(i) < high(P); L1 = min(low P+1..i-1).
- SECOND LEG: first bar k > i with low(k) < L1.
- H2 CANDIDATE: first bar m > k with close(m) > high(m-1) and close(m) < high(P).
  The setup expires if no candidate occurs with m - P <= 24. The candidate is the setup's only
  shot (used up whether or not it trades). PL = min(low P+1..m).
- ENTRY at m only if (1) (high(P)-PL)/high(P) >= 0.010, (2) (close(m)-PL)/close(m) <= 0.025,
  (3) EMA20(m) > EMA20(m-4), (4) ATRp(m) >= 0.004, (5) pair flat (engine). Fills at open(m+1).
  PL and the time of bar P travel in the enter_tag ("h2pb:<PL>:<P epoch seconds>").
- STOP: d = max(1 - PL/E, 0.008) at the fill, frozen; stop price E*(1-d), custom_stoploss
  (native -0.10 only as backstop).
- TARGET: T = E*(1 + 1.5*d), in custom_exit from current_profit (>= 1.5*d).
- TIME EXIT: 12 h (48 bars) after the fill bar, in custom_exit.
- RE-ARM: after an exit, only a setup bar P at or after the exit time can start a new setup;
  enforced in confirm_trade_entry from the P time carried in the tag.
- Warm-up 400 bars.
"""

import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

SETUP_HIGH_LOOKBACK = 24
MAX_SETUP_LIFE = 24
EMA_LENGTH = 20
EMA_SLOPE_LAG = 4
ATR_LENGTH = 14
ATR_PCT_MIN = 0.004
MIN_PULLBACK_DEPTH = 0.010
MAX_ENTRY_TO_PL = 0.025
MIN_STOP_DISTANCE = 0.008
TARGET_R = 1.5
TIME_EXIT_HOURS = 12  # 48 bars of 15m
TAG_PREFIX = "h2pb:"


def ema_talib(values: np.ndarray, length: int) -> np.ndarray:
    """EMA with the TA-Lib convention: first value (index length-1) is the SMA of the first
    `length` values, then ema = ema_prev + alpha * (x - ema_prev), alpha = 2 / (length + 1)."""
    n = len(values)
    out = np.full(n, np.nan)
    if n < length:
        return out
    alpha = 2.0 / (length + 1.0)
    prev = float(np.mean(values[:length]))
    out[length - 1] = prev
    for i in range(length, n):
        prev = prev + alpha * (values[i] - prev)
        out[i] = prev
    return out


def atr_talib(high: np.ndarray, low: np.ndarray, close: np.ndarray, length: int) -> np.ndarray:
    """Wilder ATR with the TA-Lib convention: TR starts at index 1, first ATR (index `length`)
    is the mean of TR[1..length], then atr = (atr_prev * (length - 1) + TR) / length."""
    n = len(close)
    out = np.full(n, np.nan)
    if n <= length:
        return out
    prev_close = close[:-1]
    tr = np.full(n, np.nan)
    tr[1:] = np.maximum.reduce(
        [high[1:] - low[1:], np.abs(high[1:] - prev_close), np.abs(low[1:] - prev_close)]
    )
    prev = float(np.mean(tr[1:length + 1]))
    out[length] = prev
    for i in range(length + 1, n):
        prev = (prev * (length - 1) + tr[i]) / length
        out[i] = prev
    return out


class BrooksH2Pullback_H132_v1(IStrategy):
    """Brooks H2 two-legged pullback after a fresh 24-bar high, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 400

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        n = len(dataframe)
        open_ = dataframe["open"].to_numpy(dtype=float)
        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)

        dataframe["ema20"] = ema_talib(close, EMA_LENGTH)
        atr = atr_talib(high, low, close, ATR_LENGTH)
        dataframe["atr14"] = atr
        with np.errstate(divide="ignore", invalid="ignore"):
            dataframe["atrp"] = atr / close

        # setup bar: high above the highest high of the previous 24 bars (current bar excluded)
        prev_max = dataframe["high"].shift(1).rolling(SETUP_HIGH_LOOKBACK).max().to_numpy(dtype=float)
        with np.errstate(invalid="ignore"):
            is_setup = np.isfinite(prev_max) & np.isfinite(high) & (high > prev_max)
        dataframe["h2_setup"] = is_setup

        if n:
            seconds = (
                (pd.to_datetime(dataframe["date"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC"))
                / pd.Timedelta(seconds=1)
            ).to_numpy(dtype=float)
        else:
            seconds = np.array([])

        # setup state machine, strictly backwards in time
        cand = np.zeros(n, dtype=bool)
        cand_pl = np.full(n, np.nan)
        cand_phigh = np.full(n, np.nan)
        cand_ptime = np.full(n, np.nan)
        active = False
        p = -1
        stage = 0
        l1 = math.inf
        run_min = math.inf
        for t in range(n):
            if is_setup[t]:
                active = True
                p = t
                stage = 0
                l1 = math.inf
                run_min = math.inf
                continue
            if not active:
                continue
            if t - p > MAX_SETUP_LIFE:
                active = False
                continue
            if not (
                math.isfinite(open_[t]) and math.isfinite(high[t])
                and math.isfinite(low[t]) and math.isfinite(close[t])
            ):
                continue
            prev_min = run_min
            run_min = min(run_min, low[t])
            if stage == 0:
                if t >= p + 2 and high[t] > high[t - 1] and high[t] < high[p]:
                    l1 = prev_min
                    stage = 1
            elif stage == 1:
                if low[t] < l1:
                    stage = 2
            else:
                if close[t] > high[t - 1] and close[t] < high[p]:
                    cand[t] = True
                    cand_pl[t] = run_min
                    cand_phigh[t] = high[p]
                    cand_ptime[t] = seconds[p]
                    active = False  # the candidate is the setup's only shot

        dataframe["h2_cand"] = cand
        dataframe["h2_pl"] = cand_pl
        dataframe["h2_phigh"] = cand_phigh
        dataframe["h2_ptime"] = cand_ptime
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pl = dataframe["h2_pl"]
        phigh = dataframe["h2_phigh"]
        close = dataframe["close"]
        ema_lag = dataframe["ema20"].shift(EMA_SLOPE_LAG)
        ok = (
            dataframe["h2_cand"].fillna(False).astype(bool)
            & pl.notna()
            & phigh.notna()
            & dataframe["h2_ptime"].notna()
            & dataframe["ema20"].notna()
            & ema_lag.notna()
            & dataframe["atrp"].notna()
            & (dataframe["volume"] > 0)
            & ((phigh - pl) / phigh >= MIN_PULLBACK_DEPTH)
            & ((close - pl) / close <= MAX_ENTRY_TO_PL)
            & (dataframe["ema20"] > ema_lag)
            & (dataframe["atrp"] >= ATR_PCT_MIN)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            tags = [
                f"{TAG_PREFIX}{float(a)!r}:{int(round(float(b)))}"
                for a, b in zip(pl[ok], dataframe.loc[ok, "h2_ptime"])
            ]
            dataframe.loc[ok, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the target and the time exit.
        return dataframe

    @staticmethod
    def _parse_tag(tag):
        """Return (pullback_low, setup_bar_epoch_seconds) or None."""
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        parts = tag[len(TAG_PREFIX):].split(":")
        if len(parts) != 2:
            return None
        try:
            pl = float(parts[0])
            ptime = int(parts[1])
        except ValueError:
            return None
        if not (math.isfinite(pl) and pl > 0):
            return None
        return pl, ptime

    def _stop_distance(self, trade):
        parsed = self._parse_tag(trade.enter_tag)
        entry = trade.open_rate
        if parsed is None or not entry:
            return None
        return max(1.0 - parsed[0] / entry, MIN_STOP_DISTANCE)

    def confirm_trade_entry(
        self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
        current_time, entry_tag, side: str, **kwargs
    ) -> bool:
        # Re-arm: only a setup bar at or after the last exit may start a new setup.
        parsed = self._parse_tag(entry_tag)
        if parsed is None:
            return True
        from freqtrade.persistence import Trade

        setup_time = datetime.fromtimestamp(parsed[1], tz=timezone.utc)
        for closed in Trade.get_trades_proxy(pair=pair, is_open=False):
            closed_at = closed.close_date_utc
            if closed_at is not None and setup_time < closed_at:
                return False
        return True

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        distance = self._stop_distance(trade)
        if distance is None or not current_rate:
            return None  # fall back to the native backstop
        stop_price = trade.open_rate * (1.0 - distance)
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            # price already at or below the frozen stop: stop out as soon as possible
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        distance = self._stop_distance(trade)
        if distance is not None and current_profit >= TARGET_R * distance:
            return "take_profit_1p5R"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
