"""H-115: 15m SMT divergence. BTC sweeps its 12-hour low while the alt holds; buy the alt's 4-bar structure break.

Chart 15m, UTC, closed bars only; a signal at the close of bar t fills at the open of t+1. Spot, long only.
Reference B = BTC/USDT for every traded pair X except BTC/USDT, whose B = ETH/USDT (informative 15m pair,
aligned on the candle date). If any B value needed at bar t is NaN, bar t gives no setup and no entry.

For a series S: PL_S(t) = min low over bars t-52..t-5 (48 bars, the last 4 excluded);
SL4_S(t) = min low over bars t-3..t.
SETUP at bar s: SL4_B(s) < 0.998 * PL_B(s)  AND  SL4_X(s) >= PL_X(s).
A setup at s is armed on bars s..s+8. An entry signal at bar t consumes every setup at bars <= t.
ENTRY signal at the close of an armed bar t when all hold:
  (1) close_X(t) > max high of X over bars t-4..t-1
  (2) close_B(t) > close_B(t-1)
  (3) LL = min low of X over bars t-12..t; d = (close_X(t) - LL) / close_X(t); d below 0.008 is raised to
      0.008; d above 0.03 gives no signal on this bar (setup not consumed).
Consumption follows the signal column, whether or not the order fills. d is stored in the entry tag (frozen).
FILL at the open of t+1 only if fewer than 2 trades on X were opened in the UTC day of the fill
(confirm_trade_entry); the engine allows one position per pair.
STOP: fixed d below the entry price E, E*(1-d), through custom_stoploss (native stoploss -0.03 is the backstop).
TAKE-PROFIT: E*(1+1.5*d), evaluated in custom_exit from current_profit.
TIME EXIT: 48 bars (12 hours) after the fill bar opens, in custom_exit.
"""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy

BAR = timedelta(minutes=15)
REFERENCE_PAIR = "BTC/USDT"
REFERENCE_PAIR_FOR_BTC = "ETH/USDT"
TRADED_REFERENCE_TIMEFRAME = "15m"
PRIOR_LOW_WINDOW = 48
PRIOR_LOW_NEAR_OFFSET = 5  # PL covers bars t-52..t-5
RECENT_LOW_BARS = 4
SWEEP_FACTOR = 0.998
ARMED_BARS_AFTER_SETUP = 8
STRUCTURE_BREAK_BARS = 4
STOP_LOOKBACK_BARS = 13  # LL = min low over bars t-12..t
MIN_STOP_PCT = 0.008
MAX_STOP_PCT = 0.03
TAKE_PROFIT_R = 1.5
TIME_EXIT_BARS = 48
MAX_ENTRIES_PER_UTC_DAY = 2
TAG_PREFIX = "smt"


def reference_pair_for(pair: str) -> str:
    """BTC/USDT is the reference for every pair except BTC/USDT itself, which uses ETH/USDT."""
    if pair == REFERENCE_PAIR:
        return REFERENCE_PAIR_FOR_BTC
    return REFERENCE_PAIR


def utc_day(value) -> pd.Timestamp:
    """UTC calendar day of a timestamp (naive timestamps are taken as UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.floor("D")


def make_tag(d: float) -> str:
    return f"{TAG_PREFIX}|{float(d)!r}"


def parse_tag(tag) -> float | None:
    """Frozen stop distance d recorded in an entry tag, or None for a tag this strategy did not write."""
    if not isinstance(tag, str):
        return None
    parts = tag.split("|")
    if len(parts) != 2 or parts[0] != TAG_PREFIX:
        return None
    try:
        value = float(parts[1])
    except ValueError:
        return None
    if not np.isfinite(value) or value <= 0:
        return None
    return value


def align_reference(dataframe: DataFrame, reference: DataFrame | None, column: str) -> pd.Series:
    """Reference series aligned on the candle date; NaN where the reference has no candle."""
    if reference is None or len(reference) == 0 or column not in reference:
        return pd.Series(np.nan, index=dataframe.index, dtype=float)
    series = reference.drop_duplicates("date").set_index("date")[column]
    return dataframe["date"].map(series).astype(float)


def smt_indicators(dataframe: DataFrame, reference: DataFrame | None) -> DataFrame:
    """Add the SMT columns. Every window looks backwards only (levels the current bar is compared
    with are shifted by one bar or by the stated offset)."""
    low = dataframe["low"].astype(float)
    high = dataframe["high"].astype(float)
    close = dataframe["close"].astype(float)

    b_low = align_reference(dataframe, reference, "low")
    b_close = align_reference(dataframe, reference, "close")

    # PL(t) = min low over t-52..t-5: window of 48 ending at t-5.
    pl_x = low.shift(PRIOR_LOW_NEAR_OFFSET).rolling(PRIOR_LOW_WINDOW).min()
    pl_b = b_low.shift(PRIOR_LOW_NEAR_OFFSET).rolling(PRIOR_LOW_WINDOW).min()
    # SL4(t) = min low over t-3..t.
    sl4_x = low.rolling(RECENT_LOW_BARS).min()
    sl4_b = b_low.rolling(RECENT_LOW_BARS).min()

    valid_setup = pl_x.notna() & sl4_x.notna() & pl_b.notna() & sl4_b.notna()
    setup = valid_setup & (sl4_b < SWEEP_FACTOR * pl_b) & (sl4_x >= pl_x)

    # Structure break: max high over t-4..t-1 (current bar excluded).
    prior_high = high.shift(1).rolling(STRUCTURE_BREAK_BARS).max()
    b_close_prev = b_close.shift(1)

    ll = low.rolling(STOP_LOOKBACK_BARS).min()
    d_raw = (close - ll) / close
    d_raw = d_raw.replace([np.inf, -np.inf], np.nan)
    d = d_raw.where(d_raw >= MIN_STOP_PCT, MIN_STOP_PCT).where(d_raw.notna())

    dataframe["smt_pl_x"] = pl_x
    dataframe["smt_sl4_x"] = sl4_x
    dataframe["smt_pl_b"] = pl_b
    dataframe["smt_sl4_b"] = sl4_b
    dataframe["smt_close_b"] = b_close
    dataframe["smt_prior_high"] = prior_high
    dataframe["smt_setup"] = setup.astype(bool)
    dataframe["smt_stop_d"] = d
    dataframe["smt_break"] = (
        prior_high.notna() & (close > prior_high)
    ).fillna(False).astype(bool)
    dataframe["smt_b_up"] = (
        b_close.notna() & b_close_prev.notna() & (b_close > b_close_prev)
    ).fillna(False).astype(bool)
    dataframe["smt_d_ok"] = (d.notna() & (d <= MAX_STOP_PCT)).fillna(False).astype(bool)
    return dataframe


def armed_entry_signals(setup: np.ndarray, cond: np.ndarray) -> np.ndarray:
    """Sequential setup consumption. Bar t is armed when an unconsumed setup lies in bars t-8..t;
    an entry signal at bar t consumes every setup at bars <= t."""
    n = len(setup)
    signal = np.zeros(n, dtype=bool)
    last_setup = -10**9
    last_signal = -1
    for i in range(n):
        if setup[i]:
            last_setup = i
        if cond[i] and last_setup > last_signal and last_setup >= i - ARMED_BARS_AFTER_SETUP:
            signal[i] = True
            last_signal = i
    return signal


class SMTDivergenceSweep_H115_v1(IStrategy):
    """Buy the alt's 4-bar structure break after BTC sweeps its 12-hour low and the alt does not."""

    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = False

    minimal_roi = {"0": 100.0}
    stoploss = -0.03
    use_custom_stoploss = True
    use_exit_signal = True
    startup_candle_count = 100

    def informative_pairs(self):
        return [
            (REFERENCE_PAIR, TRADED_REFERENCE_TIMEFRAME),
            (REFERENCE_PAIR_FOR_BTC, TRADED_REFERENCE_TIMEFRAME),
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        reference_pair = reference_pair_for(metadata.get("pair", ""))
        reference = self.dp.get_pair_dataframe(pair=reference_pair, timeframe=TRADED_REFERENCE_TIMEFRAME)
        return smt_indicators(dataframe, reference)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        cond = (
            dataframe["smt_break"]
            & dataframe["smt_b_up"]
            & dataframe["smt_d_ok"]
            & dataframe["smt_stop_d"].notna()
            & dataframe["smt_close_b"].notna()
            & dataframe["close"].notna()
            & (dataframe["volume"] > 0)
        ).fillna(False)
        signal = armed_entry_signals(
            dataframe["smt_setup"].to_numpy(dtype=bool), cond.to_numpy(dtype=bool)
        )
        if signal.any():
            dataframe.loc[signal, "enter_long"] = 1
            dataframe.loc[signal, "enter_tag"] = [
                make_tag(value) for value in dataframe.loc[signal, "smt_stop_d"]
            ]
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Take-profit and time exit depend on the open trade: see custom_exit.
        return dataframe

    def confirm_trade_entry(self, pair, order_type, amount, rate, time_in_force, current_time,
                            entry_tag, side, **kwargs) -> bool:
        """Fewer than 2 trades on this pair opened in the UTC day of the fill."""
        from freqtrade.persistence import Trade

        if parse_tag(entry_tag) is None:
            return False
        today = utc_day(current_time)
        opened_today = 0
        for trade in Trade.get_trades_proxy(pair=pair):
            if utc_day(trade.open_date_utc) == today:
                opened_today += 1
        return opened_today < MAX_ENTRIES_PER_UTC_DAY

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit,
                        after_fill=False, **kwargs):
        """Fixed stop at E*(1-d). The return value is relative to current_rate, so the distance is
        converted such that the stop price stays at the entry price times (1-d)."""
        d = parse_tag(trade.enter_tag)
        if d is None or not current_rate or current_rate <= 0:
            return None
        stop_price = trade.open_rate * (1.0 - d)
        relative = 1.0 - stop_price / current_rate
        if relative <= 0:
            # Price is already at or under the stop: any tiny distance triggers it.
            return -0.0001
        return -relative

    def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        d = parse_tag(trade.enter_tag)
        if d is not None and current_profit >= TAKE_PROFIT_R * d:
            return "take_profit_1_5R"
        if current_time >= trade.open_date_utc + TIME_EXIT_BARS * BAR:
            return "time_exit_12h"
        return None
