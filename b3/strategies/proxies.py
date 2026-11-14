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


# ---------------------------------------------------------------------------------------------
# Second batch, registered 2026-11-14 AFTER the first batch's results were read (P-001/P-002 rejected, P-003
# passed exploration and validation and failed the final test). Published parameters, not tuned here.
#
# P-004 RestOfDayMomentum  - Baltussen, Da, Lammers & Martens (JFE 2021, "Hedging demand and market intraday
#                            momentum"): the return from the previous close to 30 minutes before the close
#                            predicts the last 30 minutes, in 60+ futures since 1974. P-002 used only the first
#                            half hour (Gao et al.); this uses the whole day up to the entry.
# P-005 VwapTrend1m        - Zarattini & Aziz (2023, SSRN 4631351) on QQQ with 1-MINUTE bars: long while the
#                            close is above the session VWAP, short while below, flat at the close. Here a flip
#                            takes two bars (exit, then enter), and VWAP uses tick volume (CFD data has no real
#                            volume). Catastrophic stop 1% away.
# P-006 FirstCandleOrb5m   - Zarattini & Aziz (2023, SSRN 4416622) on QQQ: trade in the direction of the first
#                            5-minute candle, stop at that candle's low/high, hold to the close (the paper's 10R
#                            target is left out: the engine has no limit exits). A doji first candle: no trade.
# ---------------------------------------------------------------------------------------------

def _prev_session_close(df: pd.DataFrame) -> pd.Series:
    order = list(dict.fromkeys(df["local_date"]))
    last = df.groupby("local_date")["close"].last()
    prev = {d: (last[order[i - 1]] if i > 0 else np.nan) for i, d in enumerate(order)}
    return df["local_date"].map(prev)


class RestOfDayMomentum(ProxyStrategy):
    name = "P-004_rest_of_day_momentum_last_half_hour"
    timeframe_min = 5
    warmup = 400
    rules = SessionRules(entry_start_after_open_min=30, entry_end_before_close_min=25, flatten_before_close_min=5)
    params = {"hold_minutes": 30, "stop_frac": 0.01}

    def indicators(self, df):
        df["rod_ret"] = df["close"] / _prev_session_close(df) - 1.0
        return df

    def decide(self, row, position):
        if position is not None or pd.isna(row.rod_ret) or row.rod_ret == 0:
            return Signal(HOLD)
        if row.minutes_to_close != self.params["hold_minutes"]:
            return Signal(HOLD)
        tick, f = self.market.tick_size, self.params["stop_frac"]
        if row.rod_ret > 0:
            return Signal(ENTER_LONG, stop_price=tick_floor(row.close * (1 - f), tick), reason="day_up_so_far")
        return Signal(ENTER_SHORT, stop_price=tick_ceil(row.close * (1 + f), tick), reason="day_down_so_far")


class VwapTrend1m(ProxyStrategy):
    name = "P-005_vwap_trend_1m"
    timeframe_min = 1
    warmup = 560          # the live window must hold the whole session (at most 540 one-minute bars)
    rules = SessionRules(entry_start_after_open_min=1, entry_end_before_close_min=5, flatten_before_close_min=1)
    params = {"stop_frac": 0.01}

    def indicators(self, df):
        typical = (df["high"] + df["low"] + df["close"]) / 3.0
        vol = df["volume"].astype(float).clip(lower=1.0)
        df["vwap"] = (typical * vol).groupby(df["local_date"]).cumsum() / vol.groupby(df["local_date"]).cumsum()
        return df

    def decide(self, row, position):
        if pd.isna(row.vwap) or row.close == row.vwap:
            return Signal(HOLD)
        above = row.close > row.vwap
        if position is None:
            tick, f = self.market.tick_size, self.params["stop_frac"]
            if above:
                return Signal(ENTER_LONG, stop_price=tick_floor(row.close * (1 - f), tick), reason="above_vwap")
            return Signal(ENTER_SHORT, stop_price=tick_ceil(row.close * (1 + f), tick), reason="below_vwap")
        if (position.volume > 0) != above:
            return Signal(EXIT, reason="crossed_vwap")
        return Signal(HOLD)


class FirstCandleOrb5m(ProxyStrategy):
    name = "P-006_first_candle_orb_5m"
    timeframe_min = 5
    warmup = 120
    rules = SessionRules(entry_start_after_open_min=5, entry_end_before_close_min=60, flatten_before_close_min=5)
    params = {}

    def decide(self, row, position):
        if position is not None or row.bar_in_day != 0 or row.close == row.open:
            return Signal(HOLD)
        tick = self.market.tick_size
        if row.close > row.open:
            stop = tick_floor(row.low, tick)
            return Signal(ENTER_LONG, stop_price=stop, reason="first_candle_up") if stop < row.close else Signal(HOLD)
        stop = tick_ceil(row.high, tick)
        return Signal(ENTER_SHORT, stop_price=stop, reason="first_candle_down") if stop > row.close else Signal(HOLD)


# ---------------------------------------------------------------------------------------------
# Third batch, registered 2026-11-14 after the diagnostics of research/tools/proxy_failure_anatomy.py
# (EXPLORATION data only; validation and final test of these markets were not looked at for this rule).
#
# P-007 RestOfDayMomentumAfterVolatileDay - P-004 traded only when the PREVIOUS session was volatile.
#   Mechanism (Baltussen et al. 2021): dealers short gamma hedge in the direction of the day's move near the
#   close, and that hedging demand is larger when volatility is high. Own measurement on exploration: P-004's
#   gross per trade after a top-tercile-range day was +0.0175% (US500), +0.0359% (USTEC), +0.0148% (US30),
#   +0.0341% (US2000), against ~0 after calm days. Markets fixed before running: US500, USTEC, US30, US2000,
#   5-minute bars. Volatile = the previous session's (high-low)/open above the 2/3 quantile of the 20
#   sessions before it (the diagnostic used 60 sessions; 20 keeps the live warm-up short and is fixed here
#   before any run). Expected frequency: about 80 trades per year per market (BELOW the 200 the owner asked
#   for; a conditioned rule trades less by construction).
# ---------------------------------------------------------------------------------------------

class RestOfDayMomentumAfterVolatileDay(RestOfDayMomentum):
    name = "P-007_rest_of_day_momentum_after_volatile_day"
    warmup = 2500         # 21 full earlier sessions of up to 108 five-minute bars, plus today
    params = {"hold_minutes": 30, "stop_frac": 0.01, "vol_lookback_days": 20, "vol_quantile": 2 / 3}

    def indicators(self, df):
        df = super().indicators(df)
        g = df.groupby("local_date")
        rng = (g["high"].max() - g["low"].min()) / g["open"].first()          # one value per session, in order
        n, q = self.params["vol_lookback_days"], self.params["vol_quantile"]
        threshold = rng.shift(2).rolling(n, min_periods=n).quantile(q)         # the n sessions before yesterday
        volatile = rng.shift(1) > threshold                                    # NaN threshold -> False
        df["prev_day_volatile"] = df["local_date"].map(volatile).fillna(False).astype(bool)
        return df

    def decide(self, row, position):
        if not row.prev_day_volatile:
            return Signal(HOLD)
        return super().decide(row, position)


RULES = {"P-001": OpeningRangeBreakout, "P-002": IntradayMomentum, "P-003": NoiseAreaMomentum,
         "P-004": RestOfDayMomentum, "P-005": VwapTrend1m, "P-006": FirstCandleOrb5m,
         "P-007": RestOfDayMomentumAfterVolatileDay}
