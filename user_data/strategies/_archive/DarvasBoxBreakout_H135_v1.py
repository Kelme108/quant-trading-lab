"""H-135: intraday Darvas box (confirmed 1-3% box), volume-backed close above the top (15m).

Rule (research/proposals/H-135.json), 15m, UTC, closed bars only, spot, long only:
- EMA200 = talib EMA(close, 200). Warm-up 1000 bars.
- BOX TOP: bar k with high(k) = max high of bars k-16..k AND high(k+1..k+3) all < high(k).
  T = high(k), known at the close of k+3. Every such k starts its own box attempt.
- BOX BOTTOM: candidate b = latest bar with the lowest low of bars k+1..j. Confirmed at the close
  of c = b+3 when low(b+1), low(b+2), low(b+3) are all > low(b). B = low(b).
  DROP the attempt if any bar k+1..c has high > T, or if not confirmed by c = k+48.
  VALID only if 0.010 <= (T-B)/T <= 0.030, else dropped. A newly confirmed valid box replaces any
  older active box on the pair; if two confirm on the same bar the one with the later k wins.
- ENTRY SIGNAL: the first bar t > c with close >= 1.002*T AND volume >= 1.5 x mean volume of bars
  k..t-1 AND close > EMA200. The box is void if any bar c+1..t-1 closes below B. The box is used
  up at its signal bar. T and B travel in enter_tag ("dbx:<T>:<B>").
- confirm_trade_entry skips the trade if the fill E <= B.
- STOP: stop price B (d = (E-B)/E frozen at the fill), custom_stoploss; native -0.10 is a backstop.
- TARGET E + 1.5*(T-B) and TIME EXIT 12 h (48 bars) in custom_exit. No other exits.
Indexing is by row (consecutive 15m candles).
"""

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy

TOP_LOOKBACK = 16
TOP_CONFIRM_BARS = 3
BOTTOM_CONFIRM_BARS = 3
BOX_MAX_FORMATION_BARS = 48
BOX_MIN_HEIGHT = 0.010
BOX_MAX_HEIGHT = 0.030
BREAKOUT_CLOSE_FACTOR = 1.002
VOLUME_MULT = 1.5
EMA_LENGTH = 200
TARGET_BOX_MULTIPLE = 1.5
TIME_EXIT_HOURS = 12  # 48 bars of 15m
TAG_PREFIX = "dbx:"


def scan_boxes(high, low, close, volume, ema, rolling_top_max):
    """Backward-looking state machine. Returns (signal, top, bottom) arrays."""
    n = len(high)
    signal = np.zeros(n, dtype=bool)
    sig_top = np.full(n, np.nan)
    sig_bottom = np.full(n, np.nan)
    pending = []  # [k, T]
    active = None  # (k, T, B)

    for i in range(n):
        # 1. entry / void check for the box that was active at the previous close
        if active is not None:
            k, top, bottom = active
            if close[i] >= BREAKOUT_CLOSE_FACTOR * top:
                window = volume[k:i]
                if (
                    np.isfinite(ema[i])
                    and close[i] > ema[i]
                    and np.isfinite(volume[i])
                    and volume[i] > 0
                    and np.all(np.isfinite(window))
                    and volume[i] >= VOLUME_MULT * window.mean()
                ):
                    signal[i] = True
                    sig_top[i] = top
                    sig_bottom[i] = bottom
                    active = None
            elif close[i] < bottom:
                active = None

        # 2. advance pending box attempts
        confirmed = []
        still = []
        for attempt in pending:
            k, top = attempt
            if high[i] > top:
                continue  # dropped
            b = i - BOTTOM_CONFIRM_BARS
            done = False
            if b >= k + 1:
                low_b = low[b]
                if (
                    np.isfinite(low_b)
                    and low_b < low[b + 1 : i + 1].min()
                    and (b == k + 1 or low_b <= low[k + 1 : b].min())
                ):
                    done = True
                    height = (top - low_b) / top
                    if BOX_MIN_HEIGHT <= height <= BOX_MAX_HEIGHT:
                        confirmed.append((k, top, low_b))
            if done:
                continue
            if i - k >= BOX_MAX_FORMATION_BARS:
                continue  # not confirmed by c = k+48
            still.append(attempt)
        pending = still
        if confirmed:
            active = max(confirmed, key=lambda item: item[0])

        # 3. start a new attempt for top bar k = i-3
        k = i - TOP_CONFIRM_BARS
        if k >= TOP_LOOKBACK:
            top = high[k]
            if (
                np.isfinite(top)
                and top >= rolling_top_max[k]
                and np.all(high[k + 1 : i + 1] < top)
            ):
                pending.append([k, top])

    return signal, sig_top, sig_bottom


class DarvasBoxBreakout_H135_v1(IStrategy):
    """Confirmed 1-3% Darvas box, volume-backed close above the top, stop at box bottom, 15m."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 1000

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema200"] = pd.Series(
            ta.EMA(dataframe, timeperiod=EMA_LENGTH), index=dataframe.index
        ).astype(float)

        high = dataframe["high"].to_numpy(dtype=float)
        low = dataframe["low"].to_numpy(dtype=float)
        close = dataframe["close"].to_numpy(dtype=float)
        volume = dataframe["volume"].to_numpy(dtype=float)
        ema = dataframe["ema200"].to_numpy(dtype=float)
        rolling_top_max = (
            dataframe["high"].astype(float).rolling(TOP_LOOKBACK + 1).max().to_numpy(dtype=float)
        )

        signal, top, bottom = scan_boxes(high, low, close, volume, ema, rolling_top_max)
        dataframe["dbx_signal"] = signal
        dataframe["dbx_top"] = top
        dataframe["dbx_bottom"] = bottom
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ok = (
            dataframe["dbx_signal"].fillna(False).astype(bool)
            & dataframe["dbx_top"].notna()
            & dataframe["dbx_bottom"].notna()
            & dataframe["ema200"].notna()
            & (dataframe["volume"] > 0)
        )
        if ok.any():
            dataframe.loc[ok, "enter_long"] = 1
            tags = [
                f"{TAG_PREFIX}{repr(float(t))}:{repr(float(b))}"
                for t, b in zip(dataframe.loc[ok, "dbx_top"], dataframe.loc[ok, "dbx_bottom"])
            ]
            dataframe.loc[ok, "enter_tag"] = tags
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No exit signals: exits are the stop, the target and the time exit.
        return dataframe

    @staticmethod
    def _parse_tag(tag):
        if not isinstance(tag, str) or not tag.startswith(TAG_PREFIX):
            return None
        parts = tag[len(TAG_PREFIX):].split(":")
        if len(parts) != 2:
            return None
        try:
            top, bottom = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        if not (np.isfinite(top) and np.isfinite(bottom)) or bottom <= 0 or top <= bottom:
            return None
        return top, bottom

    def confirm_trade_entry(
        self, pair: str, order_type: str, amount: float, rate: float,
        time_in_force: str, current_time, entry_tag, side: str, **kwargs
    ) -> bool:
        box = self._parse_tag(entry_tag)
        if box is None:
            return True
        return bool(rate > box[1])

    def custom_stoploss(
        self, pair: str, trade, current_time, current_rate: float,
        current_profit: float, after_fill: bool = False, **kwargs
    ):
        box = self._parse_tag(trade.enter_tag)
        entry = trade.open_rate
        if box is None or not entry or not current_rate:
            return None  # native backstop
        distance = (entry - box[1]) / entry  # frozen at the fill
        if distance <= 0:
            return -1e-6
        stop_price = entry * (1.0 - distance)  # = box bottom
        ratio = stop_price / current_rate - 1.0
        if ratio >= 0:
            return -1e-6
        return ratio

    def custom_exit(self, pair: str, trade, current_time, current_rate: float, current_profit: float, **kwargs):
        box = self._parse_tag(trade.enter_tag)
        entry = trade.open_rate
        if box is not None and entry:
            target_price = entry + TARGET_BOX_MULTIPLE * (box[0] - box[1])
            if current_profit >= target_price / entry - 1.0:
                return "target_1_5_box"
        if current_time - trade.open_date_utc >= timedelta(hours=TIME_EXIT_HOURS):
            return "time_exit_12h"
        return None
