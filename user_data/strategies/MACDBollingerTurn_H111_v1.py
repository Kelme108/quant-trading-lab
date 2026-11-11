"""H-111: 15m MACD-Bollinger oversold momentum turn with a volatility-scaled triple barrier.

All times UTC, closed 15m bars only; a signal at the close of bar t fills at the open of bar t+1.
Spot, long only, one position per pair (engine), no pyramiding.

Indicators (15m closes, including bar t):
- Bollinger length 100, 2.0 std (population std): %B = (close - lower) / (upper - lower).
- MACD = EMA12 - EMA26 (alpha 2/(n+1)); signal = EMA9 of MACD; hist = MACD - signal.
- s = std100 / close; ATRp = ATR14 (Wilder, alpha 1/14) / close.
Entry at the close of bar t when all hold: %B < 0.2; hist(t) > 0 and hist(t-1) <= 0; MACD(t) < 0;
ATRp >= 0.004; fewer than 4 entries filled on the pair in the UTC day of the fill (confirm_trade_entry);
one-candle cooldown after an exit (protections).
Frozen at entry from the signal bar: dTP = max(1.5 s, 0.012), dSL = max(0.75 s, 0.008).
Exits, first to occur:
- stop at E * (1 - dSL), intrabar (custom_stoploss; native stoploss -0.10 is only a backstop);
- take profit at E * (1 + dTP) (custom_exit);
- time exit 24 bars (6 h) after the entry fill (custom_exit).
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy

BB_LENGTH = 100
BB_STD = 2.0
PCTB_MAX = 0.2
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ATR_LENGTH = 14
ATRP_MIN = 0.004
TP_STD_MULT = 1.5
TP_FLOOR = 0.012
SL_STD_MULT = 0.75
SL_FLOOR = 0.008
TIME_EXIT_BARS = 24
BAR = timedelta(minutes=15)
TIME_EXIT = BAR * TIME_EXIT_BARS
MAX_ENTRIES_PER_UTC_DAY = 4
WARMUP_BARS = 500
TAG_PREFIX = "macdbb"


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def make_tag(d_tp: float, d_sl: float) -> str:
    return f"{TAG_PREFIX}|{float(d_tp)!r}|{float(d_sl)!r}"


def parse_tag(tag):
    """(dTP, dSL) recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 3 or parts[0] != TAG_PREFIX:
        return None
    try:
        d_tp = float(parts[1])
        d_sl = float(parts[2])
    except ValueError:
        return None
    if not (np.isfinite(d_tp) and np.isfinite(d_sl)) or d_tp <= 0 or d_sl <= 0:
        return None
    return d_tp, d_sl


def macd_bollinger_indicators(dataframe: DataFrame) -> DataFrame:
    """Add all indicators. Backward-looking only (rolling windows, recursive EMAs, shift(1))."""
    close = dataframe["close"].astype(float)
    high = dataframe["high"].astype(float)
    low = dataframe["low"].astype(float)

    mid = close.rolling(BB_LENGTH).mean()
    std = close.rolling(BB_LENGTH).std(ddof=0)
    upper = mid + BB_STD * std
    lower = mid - BB_STD * std
    width = (upper - lower).where((upper - lower) > 0)
    dataframe["bb_pctb"] = (close - lower) / width

    ema_fast = close.ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = close.ewm(span=MACD_SLOW, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()
    hist = macd - macd_signal
    dataframe["macd"] = macd
    dataframe["macd_hist"] = hist
    dataframe["macd_hist_prev"] = hist.shift(1)

    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / ATR_LENGTH, adjust=False).mean()
    dataframe["atrp"] = atr / close

    s = std / close
    dataframe["std_pct"] = s
    dataframe["d_tp"] = np.maximum(TP_STD_MULT * s, TP_FLOOR).where(s.notna())
    dataframe["d_sl"] = np.maximum(SL_STD_MULT * s, SL_FLOOR).where(s.notna())
    dataframe["bar_index"] = np.arange(len(dataframe))
    return dataframe


class MACDBollingerTurn_H111_v1(IStrategy):
    """Buy a fresh MACD histogram upturn below zero inside the lower Bollinger band; triple barrier."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.10  # engine backstop only; the real stop is custom_stoploss
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 500  # equals WARMUP_BARS (BB 100, MACD/ATR EMA settling)

    @property
    def protections(self):
        # One-candle cooldown: no entry fill on the bar an exit happened.
        return [{"method": "CooldownPeriod", "stop_duration_candles": 1}]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return macd_bollinger_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            dataframe["bb_pctb"].notna()
            & dataframe["macd"].notna()
            & dataframe["macd_hist"].notna()
            & dataframe["macd_hist_prev"].notna()
            & dataframe["atrp"].notna()
            & dataframe["d_tp"].notna()
            & dataframe["d_sl"].notna()
            & (dataframe["bar_index"] >= WARMUP_BARS)
            & (dataframe["bb_pctb"] < PCTB_MAX)
            & (dataframe["macd_hist"] > 0)
            & (dataframe["macd_hist_prev"] <= 0)
            & (dataframe["macd"] < 0)
            & (dataframe["atrp"] >= ATRP_MIN)
            & (dataframe["volume"] > 0)
        ).fillna(False)
        if cond.any():
            dataframe.loc[cond, "enter_long"] = 1
            dataframe.loc[cond, "enter_tag"] = [
                make_tag(tp, sl)
                for tp, sl in zip(dataframe.loc[cond, "d_tp"], dataframe.loc[cond, "d_sl"])
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Fewer than 4 entries filled on this pair in the UTC day of the fill (open and closed trades)."""
        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        count = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                count += 1
        return count < MAX_ENTRIES_PER_UTC_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Stop at E * (1 - dSL), frozen per trade, expressed relative to the current price."""
        parsed = parse_tag(trade.enter_tag)
        if parsed is None:
            return None
        _, d_sl = parsed
        if current_profit is None or not np.isfinite(current_profit) or current_profit <= -1.0:
            return None
        relative = 1.0 - (1.0 - d_sl) / (1.0 + current_profit)
        return max(relative, 1e-6)

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        parsed = parse_tag(trade.enter_tag)
        if parsed is not None:
            d_tp, _ = parsed
            open_rate = float(trade.open_rate)
            if open_rate > 0 and current_rate >= open_rate * (1.0 + d_tp):
                return "take_profit"
        if pd.Timestamp(current_time) - pd.Timestamp(trade.open_date_utc) >= TIME_EXIT:
            return "time_exit_6h"
        return None
