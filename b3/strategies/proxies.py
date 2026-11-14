"""First intraday rules for the proxy markets (b3/markets.py). Registered 2026-11-14 BEFORE any backtest of
these markets was run; parameters are the published ones, not tuned. Bind a rule to a market with
`Rule.on("US500")`. Bars must be session-only (b3.markets.session_only).

P-001 OpeningRangeBreakout  - 30-minute opening range; trade the first close outside it, stop on the
                              other side, at most one entry per day (BacktestConfig.max_entries_per_day=1).
                              Source: the classic Crabel ORB; tested on US index futures and stocks in play
                              by Zarattini, Barbon & Aziz (2024, SSRN 4729284) with 5-minute ranges.
P-002 IntradayMomentum      - Gao, Han, Li & Zhou (JFE 2018): the return from the previous session close to
                              30 minutes after the open predicts the last 30 minutes. Enter 30 minutes
                              before the close in the sign of that return; flat 5 minutes before the close
                              (the engine never holds overnight). Catastrophic stop 1% away.
P-003 NoiseAreaMomentum     - Zarattini, Aune & Barbon (2024, SSRN 4824172) on SPY: the "noise area" around
                              the day's open is the 14-day average absolute move from the open at the same
                              time of day; at every half hour go long above it and short below it; exit at a
                              half hour when the close is back beyond max(upper, VWAP) (long) or
                              min(lower, VWAP) (short); flat before the close. No volatility sizing (1 unit).
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from b3.calendar import SessionRules
from b3.markets import ProxyStrategy
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD, tick_ceil, tick_floor
from live.core.models import Signal


class OpeningRangeBreakout(ProxyStrategy):
    name = "P-001_opening_range_breakout_30m"
    timeframe_min = 5
    warmup = 120          # the live window must hold the whole session (at most 108 five-minute bars)
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=60, flatten_before_close_min=5)
    params = {"range_minutes": 30}

    def indicators(self, df):
        n = self.params["range_minutes"] // self.timeframe_min
        in_range = df["bar_in_day"] < n
        g = df.groupby("local_date")
        df["or_high"] = df["high"].where(in_range).groupby(df["local_date"]).cummax()
        df["or_low"] = df["low"].where(in_range).groupby(df["local_date"]).cummin()
        df["or_high"] = df.groupby("local_date")["or_high"].ffill()
        df["or_low"] = df.groupby("local_date")["or_low"].ffill()
        df["or_done"] = g.cumcount() >= n - 1
        return df

    def decide(self, row, position):
        if position is not None or not row.or_done or pd.isna(row.or_high):
            return Signal(HOLD)
        tick = self.market.tick_size
        if row.close > row.or_high:
            return Signal(ENTER_LONG, stop_price=tick_floor(row.or_low, tick), reason="orb_up")
        if row.close < row.or_low:
            return Signal(ENTER_SHORT, stop_price=tick_ceil(row.or_high, tick), reason="orb_down")
        return Signal(HOLD)


class IntradayMomentum(ProxyStrategy):
    name = "P-002_intraday_momentum_first_to_last_half_hour"
    timeframe_min = 5
    warmup = 400          # covers the previous session (at most 108 five-minute bars) plus today's
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=25, flatten_before_close_min=5)
    params = {"signal_minutes": 30, "hold_minutes": 30, "stop_frac": 0.01}

    def indicators(self, df):
        last_bar = df["minutes_to_close"] == 0                 # the bar that ends at the session close
        closes = df.loc[last_bar, ["local_date", "close"]].drop_duplicates("local_date").set_index("local_date")["close"]
        order = list(dict.fromkeys(df["local_date"]))
        prev = {d: (closes.get(order[i - 1], np.nan) if i > 0 else np.nan) for i, d in enumerate(order)}
        df["prev_close"] = df["local_date"].map(prev)
        n = self.params["signal_minutes"] // self.timeframe_min
        at_signal = df["bar_in_day"] == n - 1                 # the bar that closes 30 minutes after the open
        sig_close = df["close"].where(at_signal).groupby(df["local_date"]).ffill()
        df["first_ret"] = sig_close / df["prev_close"] - 1.0
        return df

    def decide(self, row, position):
        if position is not None or pd.isna(row.first_ret) or row.first_ret == 0:
            return Signal(HOLD)
        if row.minutes_to_close != self.params["hold_minutes"]:
            return Signal(HOLD)
        tick, f = self.market.tick_size, self.params["stop_frac"]
        if row.first_ret > 0:
            return Signal(ENTER_LONG, stop_price=tick_floor(row.close * (1 - f), tick), reason="first_half_hour_up")
        return Signal(ENTER_SHORT, stop_price=tick_ceil(row.close * (1 + f), tick), reason="first_half_hour_down")


class NoiseAreaMomentum(ProxyStrategy):
    name = "P-003_noise_area_momentum"
    timeframe_min = 5
    warmup = 1800         # 15 sessions of up to 108 five-minute bars, plus margin
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=30, flatten_before_close_min=5)
    params = {"lookback_days": 14, "check_every_min": 30}

    def indicators(self, df):
        move = (df["close"] / df["day_open"] - 1.0).abs()
        key = df["minute_of_day"]
        # average |move from open| at the same time of day over the PREVIOUS `lookback_days` sessions
        df["sigma"] = (move.groupby(key).transform(
            lambda s: s.shift(1).rolling(self.params["lookback_days"], min_periods=self.params["lookback_days"]).mean()))
        order = list(dict.fromkeys(df["local_date"]))
        last = df.groupby("local_date")["close"].last()
        prev = {d: (last[order[i - 1]] if i > 0 else np.nan) for i, d in enumerate(order)}
        prev_close = df["local_date"].map(prev)
        df["upper"] = np.maximum(df["day_open"], prev_close) * (1 + df["sigma"])
        df["lower"] = np.minimum(df["day_open"], prev_close) * (1 - df["sigma"])
        typical = (df["high"] + df["low"] + df["close"]) / 3.0
        vol = df["volume"].astype(float).clip(lower=1.0)
        df["vwap"] = (typical * vol).groupby(df["local_date"]).cumsum() / vol.groupby(df["local_date"]).cumsum()
        bar_close_min = df["minute_of_day"] + self.timeframe_min
        df["check"] = (bar_close_min % self.params["check_every_min"]) == 0
        return df

    def decide(self, row, position):
        if not row.check or pd.isna(row.upper) or pd.isna(row.lower):
            return Signal(HOLD)
        tick = self.market.tick_size
        if position is None:
            if row.close > row.upper:
                stop = max(row.upper, row.vwap)
                if stop < row.close:
                    return Signal(ENTER_LONG, stop_price=tick_floor(stop, tick), reason="above_noise")
            elif row.close < row.lower:
                stop = min(row.lower, row.vwap)
                if stop > row.close:
                    return Signal(ENTER_SHORT, stop_price=tick_ceil(stop, tick), reason="below_noise")
            return Signal(HOLD)
        if position.volume > 0 and row.close < max(row.upper, row.vwap):
            return Signal(EXIT, reason="back_in_noise_or_below_vwap")
        if position.volume < 0 and row.close > min(row.lower, row.vwap):
            return Signal(EXIT, reason="back_in_noise_or_above_vwap")
        return Signal(HOLD)


RULES = {"P-001": OpeningRangeBreakout, "P-002": IntradayMomentum, "P-003": NoiseAreaMomentum}
