"""WIN pattern search (owner 2026-11-16, docs/plano-busca-padroes-b3.md, paths A+B), pre-registered in
b3/config/pattern_search_b3.json before any read.

Path A: 16 families of intraday patterns x their grids x 1/5 minutes x 6 exits, simulated with the fill rules of
b3/backtest.py (a fast event loop over the signals; `fidelity` proves it gives the same trades as the official
engine before any result is looked at), ranked by the deflated Sharpe over every variant and the program's PBO.

    python -m b3.pattern_search fidelity            # engineering check: trades only, no returns printed
    python -m b3.pattern_search stage-a             # path A on exploration
    python -m b3.pattern_search stage-b             # path B on exploration (after A)
    python -m b3.pattern_search --market WDO stage-a-measured   # path A on WDO, measured costs (wdo_extension)

Results: research/b3/search/. Trials: research/b3/search/ledger.jsonl (NOT research/b3/ledger.jsonl: owner D2 a).
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3 import b3_data
from b3.calendar import SP_TZ, SessionRules
from b3.markets import market
from b3.strategy import session_features, tick_ceil, tick_floor

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "b3" / "config" / "pattern_search_b3.json"
SPLITS = ROOT / "b3" / "config" / "splits_b3.json"
OUT = ROOT / "research" / "b3" / "search"
LEDGER = OUT / "ledger.jsonl"
MARKET = "WIN"                 # --market WDO: pattern_search_b3.json wdo_extension (own folder, ledger and trial count)


def set_market(m: str) -> None:
    global MARKET, OUT, LEDGER
    MARKET = m.upper()
    OUT = ROOT / "research" / "b3" / "search" / ("" if MARKET == "WIN" else MARKET.lower())
    LEDGER = OUT / "ledger.jsonl"


def other_market() -> str:
    return "WDO" if MARKET == "WIN" else "WIN"


def load_config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise RuntimeError("pattern_search_b3.json is not approved by the owner")
    return cfg


def split_bounds(split: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    s = json.loads(SPLITS.read_text(encoding="utf-8"))
    if split == "final_test" and not s.get("final_test_unlocked"):
        raise PermissionError("the final test is locked (splits_b3.json)")
    w = s["symbols"][MARKET][split]
    end = w["end_utc"] or "2100-01-01T00:00:00Z"
    return pd.Timestamp(w["start_utc"]), pd.Timestamp(end)


# ---------------------------------------------------------------------------------------------
# Data: one frame per timeframe with session features, day bounds and WDO aligned
# ---------------------------------------------------------------------------------------------

@dataclass
class Frame:
    tf: int
    df: pd.DataFrame          # session-only bars, complete days, up to the split end
    rules: SessionRules
    cal: object
    day: np.ndarray           # session index (0, 1, ...) per bar
    now: np.ndarray           # bar close time (ns since epoch, UTC)
    entry_ok: np.ndarray      # signal bar closes inside the entry window
    flatten: np.ndarray       # the bar closes at or after the session's flatten time
    next_open_ok: np.ndarray  # the next bar starts exactly when this one closes (same session)


def _session_rules(cfg: dict) -> SessionRules:
    r = cfg["data"]["session_rules"]
    return SessionRules(r["entry_start_after_open_min"], r["entry_end_before_close_min"], r["flatten_before_close_min"])


def _session_bars(root: str, tf: int, rules: SessionRules, min_cov: float, end: pd.Timestamp):
    raw = b3_data.load_b3_bars(root, f"{tf}m")
    rolls = b3_data.roll_days(root)
    bars = b3_data.back_adjusted(raw, rolls)
    cal0 = b3_data.history_calendar(root, raw, rules)
    bars = b3_data.session_only_b3(bars, cal0, tf)
    bars = bars[bars["time"] < end].reset_index(drop=True)
    skipped = b3_data.incomplete_days(bars, cal0, tf, min_cov)
    cal = b3_data.history_calendar(root, raw, rules, skipped)
    local_day = bars["time"].dt.tz_convert(SP_TZ).dt.date
    bars = bars[~local_day.isin(skipped)].reset_index(drop=True)
    return bars, cal


def load_frame(tf: int, end: pd.Timestamp, cfg: dict | None = None) -> Frame:
    cfg = cfg or load_config()
    rules = _session_rules(cfg)
    bars, cal = _session_bars(MARKET, tf, rules, cfg["data"]["min_session_coverage"], end)
    df = session_features(bars, cal, tf)
    oth, _ = _session_bars(other_market(), tf, rules, cfg["data"]["min_session_coverage"], end)
    # "wdo_close" = the OTHER market's close (WDO for the WIN program, WIN for the WDO program: F14 and B's features)
    df = df.merge(oth[["time", "close"]].rename(columns={"close": "wdo_close"}), on="time", how="left")
    days = list(dict.fromkeys(df["local_date"]))
    di = {d: i for i, d in enumerate(days)}
    day = df["local_date"].map(di).to_numpy()
    times = df["time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    step = tf * 60 * 10**9
    now = times + step
    sess = {d: cal.session(d) for d in days}
    es = np.array([pd.Timestamp(sess[d].entry_start).value for d in df["local_date"]])
    ee = np.array([pd.Timestamp(sess[d].entry_end).value for d in df["local_date"]])
    fl = np.array([pd.Timestamp(sess[d].flatten_at).value for d in df["local_date"]])
    nxt = np.zeros(len(df), dtype=bool)
    nxt[:-1] = (times[1:] == now[:-1]) & (day[1:] == day[:-1])
    return Frame(tf, df, rules, cal, day, now, (now >= es) & (now < ee), now >= fl, nxt)


# ---------------------------------------------------------------------------------------------
# Signals: direction per bar (+1 long, -1 short, 0 nothing) at the bar's close
# ---------------------------------------------------------------------------------------------

def _prev_in_day(x: np.ndarray, day: np.ndarray, lag: int = 1, fill=np.nan) -> np.ndarray:
    out = np.full(len(x), fill, dtype=float)
    out[lag:] = x[:-lag]
    same = np.zeros(len(x), dtype=bool)
    same[lag:] = day[lag:] == day[:-lag]
    out[~same] = fill
    return out


def _cross(cond: np.ndarray, day: np.ndarray) -> np.ndarray:
    prev = np.zeros(len(cond), dtype=bool)
    prev[1:] = cond[:-1]
    first = np.ones(len(cond), dtype=bool)
    first[1:] = day[1:] != day[:-1]
    prev[first] = False
    return cond & ~prev


def _prev_sessions_stat(values: np.ndarray, day: np.ndarray, how: str, n: int = 20) -> np.ndarray:
    """Per bar: a statistic of `values` over every bar of the n sessions BEFORE the bar's session."""
    s = pd.DataFrame({"d": day, "v": values})
    ok = s["v"].notna()
    g = s[ok].groupby("d")["v"]
    agg = pd.DataFrame({"sum": g.sum(), "sq": (s[ok]["v"] ** 2).groupby(s[ok]["d"]).sum(), "n": g.count()})
    agg = agg.reindex(range(int(day.max()) + 1), fill_value=0.0)
    r = agg.rolling(n, min_periods=n).sum().shift(1)
    if how == "mean":
        val = r["sum"] / r["n"]
    elif how == "sd":
        mean = r["sum"] / r["n"]
        val = np.sqrt(np.maximum(r["sq"] / r["n"] - mean**2, 0.0))
    else:
        raise ValueError(how)
    return val.to_numpy()[day]


def _same_minute_stat(values: np.ndarray, day: np.ndarray, minute: np.ndarray, how: str, n: int = 20) -> np.ndarray:
    """Per bar: median/mean of `values` at the same minute of day over the n sessions before."""
    p = pd.DataFrame({"d": day, "m": minute, "v": values}).pivot_table(index="d", columns="m", values="v", aggfunc="first")
    p = p.reindex(range(int(day.max()) + 1))
    roll = p.rolling(n, min_periods=max(5, n // 2))
    st = (roll.median() if how == "median" else roll.mean()).shift(1)
    col = {m: i for i, m in enumerate(st.columns)}
    arr = st.to_numpy()
    return arr[day, np.array([col[m] for m in minute])]


def _vwap(df: pd.DataFrame) -> np.ndarray:
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].astype(float).clip(lower=1.0)
    g = df["local_date"]
    return ((typical * vol).groupby(g).cumsum() / vol.groupby(g).cumsum()).to_numpy()


def _session_ret(close: np.ndarray, day: np.ndarray, bars: int) -> np.ndarray:
    return close / _prev_in_day(close, day, bars) - 1.0


def _rsi(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    d = df.groupby("local_date")["close"].diff()
    up, down = d.clip(lower=0), (-d).clip(lower=0)
    g = df["local_date"]
    au = up.groupby(g).transform(lambda s: s.ewm(alpha=1 / n, adjust=False, min_periods=n).mean())
    ad = down.groupby(g).transform(lambda s: s.ewm(alpha=1 / n, adjust=False, min_periods=n).mean())
    rs = au / ad.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi[(ad == 0) & au.notna()] = 100.0
    return rsi.to_numpy()


def signal_settings(cfg: dict) -> list[tuple[str, dict]]:
    out = []
    for fam, spec in cfg["families"].items():
        if fam.startswith("_"):
            continue
        grid = spec["grid"]
        keys = list(grid)
        for combo in itertools.product(*[grid[k] for k in keys]) if keys else [()]:
            out.append((fam, dict(zip(keys, combo))))
    return out


class Signals:
    """Computes each family's direction array on a Frame, caching the shared features."""

    def __init__(self, fr: Frame) -> None:
        self.fr, self.df, self.day = fr, fr.df, fr.day
        self.c = fr.df["close"].to_numpy(float)
        self.o = fr.df["open"].to_numpy(float)
        self.h = fr.df["high"].to_numpy(float)
        self.l = fr.df["low"].to_numpy(float)
        self.v = fr.df["volume"].to_numpy(float)
        self.minute = fr.df["minute_of_day"].to_numpy()
        self.bid = fr.df["bar_in_day"].to_numpy()
        self._cache: dict = {}
        self.has_history = self.day >= 20          # 20 earlier sessions loaded

    def _get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def bars(self, minutes) -> int:
        return max(1, int(round(minutes / self.fr.tf)))

    def direction(self, fam: str, p: dict) -> np.ndarray:
        d = getattr(self, "_" + fam.split("_", 1)[0].lower())(fam, p)
        d = np.where(self.has_history, d, 0).astype(np.int8)
        return d

    def _rolling_extreme(self, n):
        def f():
            g = pd.DataFrame({"d": self.day, "h": self.h, "l": self.l})
            hi = g.groupby("d")["h"].transform(lambda s: s.shift(1).rolling(n, min_periods=n).max()).to_numpy()
            lo = g.groupby("d")["l"].transform(lambda s: s.shift(1).rolling(n, min_periods=n).min()).to_numpy()
            return hi, lo
        return self._get(("ext", n), f)

    def _f01(self, fam, p, sign=1):
        hi, lo = self._rolling_extreme(self.bars(p["N"]))
        up = _cross(self.c > hi, self.day)
        dn = _cross(self.c < lo, self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _f02(self, fam, p):
        return self._f01(fam, p, -1)

    def _vwap_z(self):
        def f():
            dev = self.c / _vwap(self.df) - 1.0
            sd = _prev_sessions_stat(dev, self.day, "sd")
            return dev / sd
        return self._get("vwapz", f)

    def _f03(self, fam, p, sign=-1):
        z, k = self._vwap_z(), p["k"]
        up = _cross(z >= k, self.day)
        dn = _cross(z <= -k, self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _f04(self, fam, p):
        return self._f03(fam, p, +1)

    def _shock(self, m, series="win"):
        def f():
            c = self.c if series == "win" else self.fr.df["wdo_close"].to_numpy(float)
            r = _session_ret(c, self.day, m)
            s = _prev_sessions_stat(np.abs(r), self.day, "mean")
            return r, s
        return self._get(("shock", series, m), f)

    def _f05(self, fam, p, sign=-1):
        r, s = self._shock(self.bars(p["M"]))
        up = _cross(r >= p["k"] * s, self.day)
        dn = _cross(r <= -p["k"] * s, self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _f06(self, fam, p):
        return self._f05(fam, p, +1)

    def _f07(self, fam, p, sign=1):
        med = self._get("volmed", lambda: _same_minute_stat(self.v, self.day, self.minute, "median"))
        spike = self.v >= p["k"] * med
        bar = np.sign(self.c - self.o).astype(int)
        return sign * np.where(spike, bar, 0)

    def _f08(self, fam, p):
        return self._f07(fam, p, -1)

    def _f09(self, fam, p):
        n = self.bars(p["R"])
        g = pd.DataFrame({"d": self.day, "h": np.where(self.bid < n, self.h, np.nan), "l": np.where(self.bid < n, self.l, np.nan)})
        orh = g.groupby("d")["h"].transform("max").to_numpy()
        orl = g.groupby("d")["l"].transform("min").to_numpy()
        done = self.bid >= n
        up = _cross(done & (self.c > orh), self.day)
        dn = _cross(done & (self.c < orl), self.day)
        return up.astype(int) - dn.astype(int)

    def _f10(self, fam, p):
        g = pd.DataFrame({"d": self.day, "h": self.h, "l": self.l})
        maxb = g.groupby("d")["h"].transform(lambda s: s.cummax().shift(1)).to_numpy()   # max up to t-1
        minb = g.groupby("d")["l"].transform(lambda s: s.cummin().shift(1)).to_numpy()
        new_hi_prev = _prev_in_day((self.h > maxb).astype(float), self.day, 1, 0.0) > 0   # bar t-1 set a new high
        new_lo_prev = _prev_in_day((self.l < minb).astype(float), self.day, 1, 0.0) > 0
        cprev = _prev_in_day(self.c, self.day, 1)
        short = new_hi_prev & (self.c < self.o) & (self.c < cprev)
        long = new_lo_prev & (self.c > self.o) & (self.c > cprev)
        return long.astype(int) - short.astype(int)

    def _f11(self, fam, p):
        rsi = self._get("rsi", lambda: _rsi(self.df))
        lo, hi = p["lo_hi"]
        return _cross(rsi < lo, self.day).astype(int) - _cross(rsi > hi, self.day).astype(int)

    def _boll(self):
        def f():
            g = self.df.groupby("local_date")["close"]
            mid = g.transform(lambda s: s.rolling(20, min_periods=20).mean()).to_numpy()
            sd = g.transform(lambda s: s.rolling(20, min_periods=20).std(ddof=0)).to_numpy()
            return mid, sd
        return self._get("boll", f)

    def _f12(self, fam, p, sign=-1):
        mid, sd = self._boll()
        up = _cross(self.c > mid + p["k"] * sd, self.day)
        dn = _cross(self.c < mid - p["k"] * sd, self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _f13(self, fam, p):
        return self._f12(fam, p, +1)

    def _f14(self, fam, p):
        r, s = self._shock(self.bars(p["M"]), "wdo")
        up = _cross(r >= p["k"] * s, self.day)       # dollar up hard -> WIN short
        dn = _cross(r <= -p["k"] * s, self.day)
        return dn.astype(int) - up.astype(int)

    def _f15(self, fam, p):
        def f():
            day_open = self.df["day_open"].to_numpy(float)
            r = self.c / day_open - 1.0
            s = _same_minute_stat(np.abs(r), self.day, self.minute, "mean")
            return r, s
        r, s = self._get("daytrend", f)
        check = ((self.minute + self.fr.tf) % 30) == 0
        return np.where(check & (r >= p["k"] * s), 1, 0) - np.where(check & (r <= -p["k"] * s), 1, 0)

    def _f16(self, fam, p):
        fast, slow = p["fast_slow"]
        g = self.df.groupby("local_date")["close"]
        ef = g.transform(lambda s: s.ewm(span=fast, adjust=False, min_periods=slow).mean()).to_numpy()
        es = g.transform(lambda s: s.ewm(span=slow, adjust=False, min_periods=slow).mean()).to_numpy()
        return _cross(ef > es, self.day).astype(int) - _cross(ef < es, self.day).astype(int)


    # ---- path C (pattern_search_b3.json path_c): rarer, fast trades ----------------------------

    def _gap(self):
        def f():
            g = self.df.groupby("local_date", sort=False)
            first_open = g["open"].first()
            last_close = g["close"].last()
            gap_by_day = (first_open / last_close.shift(1) - 1.0).to_numpy()      # per session index
            gap = gap_by_day[self.day]
            absg = pd.Series(np.abs(gap_by_day))
            s = absg.rolling(20, min_periods=20).mean().shift(1).to_numpy()[self.day]
            prev_ok = _prev_in_day(self.fr.entry_ok.astype(float), self.day, 1, 0.0) > 0
            first_in_window = self.fr.entry_ok & ~prev_ok
            return gap, s, first_in_window
        return self._get("gap", f)

    def _c01(self, fam, p, sign=-1):
        gap, s, first = self._gap()
        up = first & (gap >= p["k"] * s)
        dn = first & (gap <= -p["k"] * s)
        return sign * (up.astype(int) - dn.astype(int))

    def _c02(self, fam, p):
        return self._c01(fam, p, +1)

    def _c03(self, fam, p):
        return self._f03(fam, p, -1)

    def _c04(self, fam, p, sign=-1):
        rng = self.h - self.l
        med = self._get("rngmed", lambda: _same_minute_stat(rng, self.day, self.minute, "median"))
        shock = (rng >= p["k"] * med) & (med > 0)
        bar = np.sign(self.c - self.o).astype(int)
        return sign * np.where(shock, bar, 0)

    def _c05(self, fam, p):
        return self._c04(fam, p, +1)

    def _run_length(self, cond):
        # length of the current run of `cond` inside the session (0 where cond is false)
        out = np.zeros(len(cond), dtype=np.int64)
        for i in range(len(cond)):
            if cond[i]:
                out[i] = out[i - 1] + 1 if i and cond[i - 1] and self.day[i] == self.day[i - 1] else 1
        return out

    def _c06(self, fam, p):
        n = int(p["n"])
        up_run = self._get("runup", lambda: self._run_length(self.c > self.o))
        dn_run = self._get("rundn", lambda: self._run_length(self.c < self.o))
        return (dn_run == n).astype(int) - (up_run == n).astype(int)

    def _c07(self, fam, p):
        m = self.bars(15)
        r1, s1 = self._shock(m)
        r2, s2 = self._shock(m, "wdo")
        k = p["k"]
        up = _cross((r1 >= k * s1) & (r2 >= k * s2), self.day)
        dn = _cross((r1 <= -k * s1) & (r2 <= -k * s2), self.day)
        return dn.astype(int) - up.astype(int)

    def _c08(self, fam, p):
        return self._f07(fam, p, +1)

    def _c09(self, fam, p):
        return self._f07(fam, p, -1)

    def _c10(self, fam, p):
        def f():
            g = pd.DataFrame({"d": self.day, "h": self.h, "l": self.l})
            maxb = g.groupby("d")["h"].transform(lambda x: x.cummax().shift(1)).to_numpy()
            minb = g.groupby("d")["l"].transform(lambda x: x.cummin().shift(1)).to_numpy()
            r = self.c / self.df["day_open"].to_numpy(float) - 1.0
            s = _same_minute_stat(np.abs(r), self.day, self.minute, "mean")
            return maxb, minb, r, s
        maxb, minb, r, s = self._get("late", f)
        late = self.minute >= 16 * 60
        short = _cross(late & (self.c > maxb) & (r >= p["k"] * s), self.day)
        long = _cross(late & (self.c < minb) & (r <= -p["k"] * s), self.day)
        return long.astype(int) - short.astype(int)

    def _c11(self, fam, p):
        morning = (self.minute >= 9 * 60) & (self.minute < 12 * 60)
        g = pd.DataFrame({"d": self.day, "h": np.where(morning, self.h, np.nan), "l": np.where(morning, self.l, np.nan)})
        rh = g.groupby("d")["h"].transform("max").to_numpy()
        rl = g.groupby("d")["l"].transform("min").to_numpy()
        after = self.minute >= 12 * 60
        up = _cross(after & (self.c > rh), self.day)
        dn = _cross(after & (self.c < rl), self.day)
        return up.astype(int) - dn.astype(int)


# ---------------------------------------------------------------------------------------------
# Simulation with the fill rules of b3/backtest.py
# ---------------------------------------------------------------------------------------------

def measured_cost(name: str, cfg: dict | None = None):
    """A B3Cost from pattern_search_b3.json cost_reevaluation (measured from the Clear ticks)."""
    from dataclasses import replace
    cfg = cfg or load_config()
    c = (cfg["cost_reevaluation"] if MARKET == "WIN" else cfg["wdo_extension"]["costs"])[name]
    return replace(market(MARKET).cost("base"), name=name, fees_per_side_brl=c["fees_per_side_brl"],
                   slippage_ticks_per_side=c["slippage_ticks_per_side"], stop_extra_ticks=c["stop_extra_ticks"])


def simulate(fr: Frame, d: np.ndarray, hold_min: int, stop_frac: float, scenario,
             max_per_day: int = 8, start: pd.Timestamp | None = None) -> pd.DataFrame:
    m = market(MARKET)
    cost = scenario if not isinstance(scenario, str) else m.cost(scenario)
    inst = m.instrument()
    tick, tv, pv = inst.tick_size, inst.tick_value_brl, inst.point_value_brl
    slip = cost.slippage_ticks_per_side * tick
    cash = cost.cash_per_side_brl
    o = fr.df["open"].to_numpy(float)
    h = fr.df["high"].to_numpy(float)
    l = fr.df["low"].to_numpy(float)
    c = fr.df["close"].to_numpy(float)
    off = fr.df["adj_offset"].to_numpy(float)
    n = len(c)
    hb = max(1, int(round(hold_min / fr.tf)))
    start_ns = start.value if start is not None else -2**62
    idx = np.flatnonzero((d != 0) & fr.entry_ok)
    out = []
    free_from = 0
    per_day: dict[int, int] = {}

    def exec_at(k: int) -> float:
        return o[k + 1] if fr.next_open_ok[k] else c[k]

    for k in idx:
        if k < free_from or fr.now[k] < start_ns:
            continue
        dk = fr.day[k]
        if per_day.get(dk, 0) >= max_per_day:
            continue
        side = int(d[k])
        stop = tick_floor(c[k] * (1 - stop_frac), tick) if side > 0 else tick_ceil(c[k] * (1 + stop_frac), tick)
        entry = exec_at(k) + (slip if side > 0 else -slip)
        per_day[dk] = per_day.get(dk, 0) + 1
        e_time = fr.now[k]
        j = k + 1
        last = k + hb
        exit_px, reason, x_time, x_bar = None, None, None, None
        while j < n:
            if fr.day[j] != dk:                    # cannot happen with the flatten rule; safety
                exit_px, reason, x_time, x_bar = c[j - 1], "end_of_day", fr.now[j - 1], j - 1
                break
            if side > 0 and l[j] <= stop:
                exit_px, reason = cost.stop_fill(min(o[j], stop), "long", tick), "stop_loss"
            elif side < 0 and h[j] >= stop:
                exit_px, reason = cost.stop_fill(max(o[j], stop), "short", tick), "stop_loss"
            elif fr.flatten[j]:
                exit_px, reason = exec_at(j) + (-slip if side > 0 else slip), "end_of_day_flatten"
            elif j == last:
                exit_px, reason = exec_at(j) + (-slip if side > 0 else slip), "time_exit"
            if reason:
                x_time, x_bar = fr.now[j], j
                break
            j += 1
        if reason is None:
            exit_px, reason, x_time, x_bar = c[n - 1], "end_of_data", fr.now[n - 1], n - 1
        # after a stop the same bar's decision may enter again (engine order); after an exit order it may not
        free_from = x_bar if reason == "stop_loss" else x_bar + 1
        pts = (exit_px - entry) * side
        gross = pts / tick * tv
        net = gross - 2 * cash
        notional = (entry - off[k]) * pv
        out.append((e_time, x_time, side, entry, stop, exit_px, reason, pts, gross, net, notional, dk))
    t = pd.DataFrame(out, columns=["entry_ns", "exit_ns", "side", "entry_price", "stop_price", "exit_price", "exit_reason",
                                   "points", "gross_brl", "net_brl", "notional", "day"])
    t["gross_pct"] = t["gross_brl"] / t["notional"] * 100
    t["net_pct"] = t["net_brl"] / t["notional"] * 100
    return t


# ---------------------------------------------------------------------------------------------
# Metrics and gate
# ---------------------------------------------------------------------------------------------

def daily_returns(t: pd.DataFrame, fr: Frame, start: pd.Timestamp) -> pd.Series:
    """Net % per session (by the exit's session), 0 on sessions without a trade, over the split's sessions."""
    days = np.unique(fr.day[fr.now >= start.value])
    s = t.groupby("day")["net_pct"].sum() if len(t) else pd.Series(dtype=float)
    return s.reindex(days, fill_value=0.0)


def metrics(t: pd.DataFrame, fr: Frame, start: pd.Timestamp, years: float) -> dict:
    if not len(t):
        return {"trades": 0, "trades_per_year": 0.0}
    r = t["net_pct"].to_numpy() / 100
    eq = np.cumprod(1 + r)
    dd = float((1 - eq / np.maximum.accumulate(eq)).max() * 100)
    yr = pd.to_datetime(t["exit_ns"], utc=True).dt.tz_convert(SP_TZ).dt.year
    by_year = t.groupby(yr)["net_pct"].sum()
    best = int(np.argmax(r))
    return {"trades": int(len(t)), "trades_per_year": len(t) / years, "mean_gross_pct": float(t["gross_pct"].mean()),
            "mean_net_pct": float(t["net_pct"].mean()), "net_return_pct": float((eq[-1] - 1) * 100),
            "net_without_best_pct": float((np.prod(np.delete(1 + r, best)) - 1) * 100),
            "hit_rate": float((t["net_pct"] > 0).mean()), "max_drawdown_pct": dd,
            "positive_years_share": float((by_year > 0).mean()), "by_year_pct": {int(k): float(v) for k, v in by_year.items()},
            "stops_share": float((t["exit_reason"] == "stop_loss").mean())}


def gate(base: dict, cons: dict, dsr: float | None, pbo: float | None, g: dict) -> list[str]:
    fails = []
    if base.get("trades_per_year", 0) < g["min_trades_per_year"]:
        fails.append("trades_per_year")
    if base.get("net_return_pct", -1) <= g["net_base_pct_gt"]:
        fails.append("net_base")
    if cons.get("net_return_pct", -1) <= g["net_conservative_pct_gt"]:
        fails.append("net_conservative")
    if base.get("net_without_best_pct", -1) <= g["net_without_best_trade_gt"]:
        fails.append("net_without_best")
    if max(base.get("max_drawdown_pct", 100), cons.get("max_drawdown_pct", 100)) > g["max_drawdown_pct"]:
        fails.append("drawdown")
    if base.get("positive_years_share", 0) < g["positive_years_share"]:
        fails.append("positive_years")
    if dsr is None or not dsr >= g["deflated_sharpe_min"]:
        fails.append("deflated_sharpe")
    if pbo is None or pbo > g["pbo_max"]:
        fails.append("pbo")
    return fails


def _log(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def variant_id(fam: str, p: dict, tf: int, hold: int, stop: float) -> str:
    ps = ",".join(f"{k}={v}" for k, v in p.items())
    return f"{fam}[{ps}]@{tf}m/h{hold}/s{stop}"


# ---------------------------------------------------------------------------------------------
# Stage A
# ---------------------------------------------------------------------------------------------

def stage_a(split: str = "exploration") -> Path:
    if split != "exploration":
        raise ValueError("stage A reads exploration only; finalists go to validation through `validate`")
    cfg = load_config()
    start, end = split_bounds(split)
    years = (end - start).days / 365.25
    ex = cfg["execution"]
    rows, daily = [], {}
    trades_dir = OUT / "trades-A"
    trades_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for tf in cfg["data"]["timeframes_min"]:
        fr = load_frame(tf, end, cfg)
        sig = Signals(fr)
        for fam, p in signal_settings(cfg):
            d = sig.direction(fam, p)
            for hold, stop in itertools.product(ex["exit_grid"]["hold_min"], ex["exit_grid"]["stop_frac"]):
                vid = variant_id(fam, p, tf, hold, stop)
                tb = simulate(fr, d, hold, stop, "base", ex["max_entries_per_session"], start)
                tc = simulate(fr, d, hold, stop, "conservative", ex["max_entries_per_session"], start)
                mb, mc = metrics(tb, fr, start, years), metrics(tc, fr, start, years)
                daily[vid] = daily_returns(tb, fr, start)
                rows.append({"variant": vid, "family": fam, "params": p, "tf": tf, "hold_min": hold, "stop_frac": stop,
                             "base": mb, "conservative": mc})
                if len(tb):
                    tb.assign(variant=vid).to_csv(trades_dir / f"{hashlib.sha1(vid.encode()).hexdigest()[:12]}.csv.gz", index=False)
                _log({"variant": vid, "stage": "A", "split": split, "read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "trades": mb.get("trades", 0)})
        print(f"tf {tf}m done in {time.time() - t0:.0f}s", flush=True)
    return _finish("A", split, cfg, rows, daily, start)


def stage_a_measured() -> Path:
    """Stage A's 552 variants again, with the measured costs (cost_reevaluation); n_trials stays 561."""
    cfg = load_config()
    start, end = split_bounds("exploration")
    years = (end - start).days / 365.25
    ex = cfg["execution"]
    cm, cp = measured_cost("measured", cfg), measured_cost("measured_p90", cfg)
    rows, daily = [], {}
    for tf in cfg["data"]["timeframes_min"]:
        fr = load_frame(tf, end, cfg)
        sig = Signals(fr)
        for fam, p in signal_settings(cfg):
            d = sig.direction(fam, p)
            for hold, stop in itertools.product(ex["exit_grid"]["hold_min"], ex["exit_grid"]["stop_frac"]):
                vid = variant_id(fam, p, tf, hold, stop)
                tb = simulate(fr, d, hold, stop, cm, ex["max_entries_per_session"], start)
                tc = simulate(fr, d, hold, stop, cp, ex["max_entries_per_session"], start)
                daily[vid] = daily_returns(tb, fr, start)
                rows.append({"variant": vid, "family": fam, "params": p, "tf": tf, "hold_min": hold, "stop_frac": stop,
                             "base": metrics(tb, fr, start, years), "conservative": metrics(tc, fr, start, years),
                             "_scenarios": {"base": "measured", "conservative": "measured_p90"}})
                _log({"variant": vid, "stage": "A-measured", "split": "exploration",
                      "read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "trades": rows[-1]["base"].get("trades", 0)})
        print(f"tf {tf}m done", flush=True)
    if MARKET != "WIN":                     # wdo_extension: its own program, one read per variant
        return _finish("A-measured", "exploration", cfg, rows, daily, start)
    b = json.loads((OUT / "B-exploration.json").read_text(encoding="utf-8"))
    return _finish("A-measured", "exploration", cfg, rows, daily, start, prior_trials=b["n_variants"])


def stage_c() -> Path:
    """Path C (pattern_search_b3.json path_c) on exploration for MARKET, measured costs."""
    cfg = load_config()
    pc = cfg["path_c"]
    start, end = split_bounds("exploration")
    years = (end - start).days / 365.25
    ex = cfg["execution"]
    cm, cp = measured_cost("measured", cfg), measured_cost("measured_p90", cfg)
    rows, daily = [], {}
    for tf in pc["timeframes_min"]:
        fr = load_frame(tf, end, cfg)
        sig = Signals(fr)
        for fam, p in signal_settings({"families": pc["families"]}):
            d = sig.direction(fam, p)
            for hold, stop in itertools.product(ex["exit_grid"]["hold_min"], ex["exit_grid"]["stop_frac"]):
                vid = variant_id(fam, p, tf, hold, stop)
                tb = simulate(fr, d, hold, stop, cm, ex["max_entries_per_session"], start)
                tc = simulate(fr, d, hold, stop, cp, ex["max_entries_per_session"], start)
                daily[vid] = daily_returns(tb, fr, start)
                rows.append({"variant": vid, "family": fam, "params": p, "tf": tf, "hold_min": hold, "stop_frac": stop,
                             "base": metrics(tb, fr, start, years), "conservative": metrics(tc, fr, start, years),
                             "_scenarios": {"base": "measured", "conservative": "measured_p90"}})
                _log({"variant": vid, "stage": "C", "split": "exploration",
                      "read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "trades": rows[-1]["base"].get("trades", 0)})
        print(f"tf {tf}m done", flush=True)
    from lab import stats
    prior = pd.read_csv(OUT / "A-measured-exploration-daily.csv.gz", index_col=0)
    prior_sharpes = [stats.sharpe(prior[c].to_numpy()) for c in prior.columns]
    prior_trials = 561 if MARKET == "WIN" else 552
    if MARKET == "WIN":                       # B's 9 variants: their Sharpes come from B's daily matrix
        b = pd.read_csv(OUT / "B-exploration-daily.csv.gz", index_col=0)
        prior_sharpes += [stats.sharpe(b[c].to_numpy()) for c in b.columns]
    g = dict(cfg["gate_search"], min_trades_per_year=pc["gate"]["min_trades_per_year"])
    return _finish("C", "exploration", dict(cfg, gate_search=g), rows, daily, start, prior_trials=prior_trials,
                   prior_sharpes=prior_sharpes)


def _finish(stage: str, split: str, cfg: dict, rows: list, daily: dict, start, prior_trials: int = 0,
            prior_sharpes: list | None = None) -> Path:
    from lab import stats
    keys = list(daily)
    mat = pd.DataFrame({k: daily[k] for k in keys}).fillna(0.0)
    n_trials = prior_trials + len(keys)
    sharpes = [stats.sharpe(mat[k].to_numpy()) for k in keys] + list(prior_sharpes or [])
    var = float(np.var(sharpes, ddof=1)) if len(sharpes) > 1 else 0.0       # across EVERY trial of the program
    pbo = stats.pbo_cscv(mat.to_numpy(), n_slices=16) if len(keys) >= 2 else None
    g = cfg["gate_search"]
    for r in rows:
        ds = stats.deflated_sharpe(mat[r["variant"]].to_numpy(), n_trials, var)
        r["deflated_sharpe"] = ds
        r["fails"] = gate(r["base"], r["conservative"], ds["dsr"], pbo["pbo"] if pbo else None, g)
        r["passed"] = not r["fails"]
    rows.sort(key=lambda r: -(r["deflated_sharpe"]["dsr"] if r["deflated_sharpe"]["dsr"] == r["deflated_sharpe"]["dsr"] else -1))
    out = {"stage": stage, "split": split, "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "config": "b3/config/pattern_search_b3.json", "n_variants": len(keys), "n_trials_for_dsr": n_trials,
           "variance_of_trial_sharpes": var, "pbo": pbo, "passed": [r["variant"] for r in rows if r["passed"]],
           "rows": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{stage}-{split}.json"
    path.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    mat.to_csv(OUT / f"{stage}-{split}-daily.csv.gz")
    return path


# ---------------------------------------------------------------------------------------------
# Stage B: frequent base signal + LightGBM filter, walk-forward by quarter (pattern_search_b3.json path_b)
# ---------------------------------------------------------------------------------------------

def features(fr: Frame) -> pd.DataFrame:
    """Causal features at the close of every bar (pattern_search_b3.json path_b.features)."""
    from b3.events import mark_events
    df, day, tf = fr.df, fr.day, fr.tf
    c = df["close"].to_numpy(float)
    o = df["open"].to_numpy(float)
    v = df["volume"].to_numpy(float)
    minute = df["minute_of_day"].to_numpy()
    g = df["local_date"]
    bars = lambda m: max(1, int(round(m / tf)))  # noqa: E731
    r1 = c / _prev_in_day(c, day, 1) - 1.0
    vol30 = pd.Series(r1).groupby(day).transform(lambda x: x.rolling(bars(30), min_periods=max(2, bars(30) // 2)).std()).to_numpy()
    hi = df.groupby(g)["high"].cummax().to_numpy()
    lo = df.groupby(g)["low"].cummin().to_numpy()
    last_close = df.groupby(g)["close"].last()
    first_open = df.groupby(g)["open"].first()
    order = list(dict.fromkeys(g))
    prev_ret = {d: (last_close[order[i - 1]] / first_open[order[i - 1]] - 1.0 if i else np.nan) for i, d in enumerate(order)}
    gap = {d: (first_open[d] / last_close[order[i - 1]] - 1.0 if i else np.nan) for i, d in enumerate(order)}
    wdo = df["wdo_close"].to_numpy(float)
    wdo_open = pd.Series(wdo).groupby(day).transform("first").to_numpy()
    ev = mark_events(df[["time"]], ["FOMC", "CPI", "NFP"], tf)
    med = _same_minute_stat(v, day, minute, "median")
    out = pd.DataFrame({
        "minute_of_day": minute, "weekday": df["time"].dt.tz_convert(SP_TZ).dt.weekday.to_numpy(),
        "bar_ret": c / o - 1.0, "ret_open": c / df["day_open"].to_numpy(float) - 1.0,
        "ret_15": _session_ret(c, day, bars(15)), "ret_60": _session_ret(c, day, bars(60)), "vol_30": vol30,
        "vol_ratio": v / med, "dist_vwap": c / _vwap(df) - 1.0, "dist_high": c / hi - 1.0, "dist_low": c / lo - 1.0,
        "prev_session_ret": g.map(prev_ret).to_numpy(float), "open_gap": g.map(gap).to_numpy(float),
        "wdo_ret_15": _session_ret(wdo, day, bars(15)), "wdo_ret_open": wdo / wdo_open - 1.0,
        "fomc_day": ev["FOMC_today"].astype(int).to_numpy(), "cpi_day": ev["CPI_today"].astype(int).to_numpy(),
        "nfp_day": ev["NFP_today"].astype(int).to_numpy()})
    return out


def _quarters(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    q = pd.Timestamp(year=start.year, month=3 * ((start.month - 1) // 3) + 1, day=1, tz=SP_TZ)
    out = []
    while q < end:
        out.append(q.tz_convert("UTC"))
        q = q + pd.DateOffset(months=3)
    return out


def _model(cfg: dict):
    import lightgbm as lgb
    m = dict(cfg["path_b"]["model"])
    m.pop("library", None)
    m.pop("objective", None)
    return lgb.LGBMClassifier(objective="binary", verbose=-1, **m)


def select_bases(a_rows: list, cfg: dict) -> list[dict]:
    eligible = [r for r in a_rows if r["base"].get("trades_per_year", 0) >= 1000]
    eligible.sort(key=lambda r: -r["base"].get("mean_gross_pct", -9))
    picked, fams = [], set()
    for r in eligible:
        if r["family"] in fams:
            continue
        picked.append(r)
        fams.add(r["family"])
        if len(picked) == 3:
            break
    return picked


def predict_walk_forward(fr: Frame, d: np.ndarray, base_row: dict, cfg: dict, start: pd.Timestamp,
                         end: pd.Timestamp) -> tuple[np.ndarray, pd.Timestamp]:
    """Probability for every signal bar of every predicted quarter; NaN elsewhere. Returns (prob, first predicted)."""
    feats = features(fr)
    ex = cfg["execution"]
    tc = simulate(fr, d, base_row["hold_min"], base_row["stop_frac"], "conservative", ex["max_entries_per_session"], start)
    bar_of = np.searchsorted(fr.now, tc["entry_ns"].to_numpy())
    y = (tc["net_pct"] > 0).astype(int).to_numpy()
    X_tr_all = feats.iloc[bar_of].assign(side=tc["side"].to_numpy()).reset_index(drop=True)
    exit_ns = tc["exit_ns"].to_numpy()
    prob = np.full(len(d), np.nan)
    first_pred = start + pd.DateOffset(months=12)
    sig_bars = np.flatnonzero(d != 0)
    qs = _quarters(start, end)
    first_q = None
    for i, q in enumerate(qs):
        if q < first_pred:
            continue
        q_end = qs[i + 1] if i + 1 < len(qs) else end
        train = exit_ns < q.value
        if train.sum() < 200 or len(set(y[train])) < 2:
            continue
        model = _model(cfg).fit(X_tr_all[train], y[train])
        in_q = sig_bars[(fr.now[sig_bars] >= q.value) & (fr.now[sig_bars] < q_end.value)]
        if len(in_q):
            Xq = feats.iloc[in_q].assign(side=d[in_q].astype(int))
            prob[in_q] = model.predict_proba(Xq)[:, 1]
        first_q = first_q or q
    return prob, first_q


def stage_b() -> Path:
    cfg = load_config()
    start, end = split_bounds("exploration")
    a = json.loads((OUT / "A-exploration.json").read_text(encoding="utf-8"))
    bases = select_bases(a["rows"], cfg)
    ex = cfg["execution"]
    rows, daily = [], {}
    frames: dict = {}
    trades_dir = OUT / "trades-B"
    trades_dir.mkdir(parents=True, exist_ok=True)
    pred_start = None
    for br in bases:
        tf = br["tf"]
        fr = frames.get(tf) or frames.setdefault(tf, load_frame(tf, end, cfg))
        d = Signals(fr).direction(br["family"], br["params"])
        prob, first_q = predict_walk_forward(fr, d, br, cfg, start, end)
        pred_start = first_q if pred_start is None else max(pred_start, first_q)
        for th in cfg["path_b"]["thresholds"]:
            df_ = np.where(np.nan_to_num(prob, nan=-1.0) >= th, d, 0).astype(np.int8)
            vid = f"B:{br['variant']}|p>={th}"
            tb = simulate(fr, df_, br["hold_min"], br["stop_frac"], "base", ex["max_entries_per_session"], first_q)
            tcn = simulate(fr, df_, br["hold_min"], br["stop_frac"], "conservative", ex["max_entries_per_session"], first_q)
            years = (end - first_q).days / 365.25
            mb, mc = metrics(tb, fr, first_q, years), metrics(tcn, fr, first_q, years)
            daily[vid] = daily_returns(tb, fr, first_q)
            rows.append({"variant": vid, "family": br["family"], "base_variant": br["variant"], "threshold": th, "tf": tf,
                         "hold_min": br["hold_min"], "stop_frac": br["stop_frac"], "predicted_from": str(first_q),
                         "base": mb, "conservative": mc,
                         "unfiltered_base_same_period": metrics(simulate(fr, d, br["hold_min"], br["stop_frac"], "base",
                                                                         ex["max_entries_per_session"], first_q), fr, first_q, years)})
            if len(tb):
                tb.assign(variant=vid).to_csv(trades_dir / f"{hashlib.sha1(vid.encode()).hexdigest()[:12]}.csv.gz", index=False)
            _log({"variant": vid, "stage": "B", "split": "exploration", "read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "trades": mb.get("trades", 0)})
    from lab import stats
    a_daily = pd.read_csv(OUT / "A-exploration-daily.csv.gz", index_col=0)
    return _finish("B", "exploration", cfg, rows, daily, pred_start, prior_trials=a["n_variants"],
                   prior_sharpes=[stats.sharpe(a_daily[c].to_numpy()) for c in a_daily.columns])


# ---------------------------------------------------------------------------------------------
# Fidelity: the fast simulator against the official engine (trades only)
# ---------------------------------------------------------------------------------------------

def fidelity(n_variants: int = 3, scenario: str = "base") -> dict:
    from b3.backtest import BacktestConfig, run
    from b3.markets import ProxyStrategy
    from live.core.models import Signal

    cfg = load_config()
    start, end = split_bounds("exploration")
    picks = [("F01_breakout_follow", {"N": 30}, 5, 30, 0.003), ("F05_shock_fade", {"M": 15, "k": 2.0}, 1, 15, 0.006),
             ("F11_rsi_fade", {"lo_hi": [25, 75]}, 5, 60, 0.003)][:n_variants]
    report = []
    TICK = market(MARKET).instrument().tick_size
    for fam, p, tf, hold, stop in picks:
        fr = load_frame(tf, end, cfg)
        d = Signals(fr).direction(fam, p)
        sim = simulate(fr, d, hold, stop, scenario, cfg["execution"]["max_entries_per_session"], start)
        hb = max(1, int(round(hold / tf)))
        frame = fr.df.copy()
        frame["sig"] = d
        frame["ok_start"] = fr.now >= start.value

        class Rule(ProxyStrategy):
            name = "search-fidelity"
            symbol = MARKET
            timeframe_min = tf
            warmup = 1
            rules = fr.rules
            params = {}

            def __init__(self):
                super().__init__(calendar=fr.cal)
                self.held = 0

            def indicators(self, df):
                df["sig"] = frame["sig"].to_numpy()
                df["ok_start"] = frame["ok_start"].to_numpy()
                return df

            def decide(self, row, position):
                if position is not None:
                    self.held += 1
                    return Signal("exit", reason="time_exit") if self.held >= hb else Signal("hold")
                self.held = 0
                if not row.ok_start or row.sig == 0:
                    return Signal("hold")
                if row.sig > 0:
                    return Signal("enter", stop_price=tick_floor(row.close * (1 - stop), TICK))
                return Signal("enter_short", stop_price=tick_ceil(row.close * (1 + stop), TICK))

        cols = ["time", "open", "high", "low", "close", "volume"]
        res = run(fr.df[cols].reset_index(drop=True), Rule(), market(MARKET).cost(scenario),
                  BacktestConfig(max_entries_per_day=cfg["execution"]["max_entries_per_session"]), market(MARKET).instrument())
        off = pd.DataFrame([(t.entry_time.value, t.entry_price, t.exit_time.value, round(t.exit_price, 6)) for t in res.trades],
                           columns=["e", "ep", "x", "xp"])
        mine = pd.DataFrame({"e": sim["entry_ns"], "ep": sim["entry_price"], "x": sim["exit_ns"], "xp": sim["exit_price"].round(6)})
        a, b = set(map(tuple, off.to_numpy())), set(map(tuple, mine.to_numpy()))
        same = len(a & b)
        report.append({"variant": variant_id(fam, p, tf, hold, stop), "official_trades": len(a), "simulated_trades": len(b),
                       "identical": same, "identical_share": same / max(len(a), len(b), 1)})
        print(report[-1], flush=True)
    out = {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "scenario": scenario,
           "note": "trades compared by entry/exit time and price only; no return was looked at", "variants": report}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fidelity.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.pattern_search")
    ap.add_argument("--market", default="WIN", choices=("WIN", "WDO"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fidelity")
    sub.add_parser("stage-a")
    sub.add_parser("stage-b")
    sub.add_parser("stage-a-measured")
    sub.add_parser("stage-c")
    a = ap.parse_args(argv)
    set_market(a.market)
    if a.market != "WIN" and a.cmd not in ("fidelity", "stage-a-measured", "stage-c"):
        raise SystemExit("WDO: only fidelity and stage-a-measured are pre-registered (wdo_extension)")
    if a.cmd == "fidelity":
        r = fidelity()
        return 0 if all(v["identical_share"] >= 0.99 for v in r["variants"]) else 1
    if a.cmd == "stage-a":
        print(stage_a())
    if a.cmd == "stage-b":
        print(stage_b())
    if a.cmd == "stage-a-measured":
        print(stage_a_measured())
    if a.cmd == "stage-c":
        print(stage_c())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
