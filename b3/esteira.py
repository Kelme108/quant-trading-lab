"""Strategy conveyor ('esteira', b3/config/esteira_b3.json, owner 2026-11-17 'tudo aprovado').

A FAMILY is one simple idea with at most 3 parameters and a small grid, written as a Python file in
b3/families/ that defines `FAMILIES = [Family(...), ...]`. A family's `signal(ctx, p)` returns, for every bar,
+1 (buy), -1 (sell) or 0 at the bar's CLOSE, using only `ctx` (bars, session features, helpers). It must be
causal; `check_family` proves it before any result is read.

Every variant (family x grid point x timeframe) is simulated on EXPLORATION with ONE default exit (target/stop in
BRL + time limit) replayed on 1-minute bars, at the measured cost. The screen keeps rules that are "not bad and
not over-fitted": frequent, positive at the measured cost, positive in most time slices, on a plateau of positive
neighbours, the best one per family, and not the same bet as a rule already selected.

    python -m b3.esteira screen                 # every family not screened yet, WIN and WDO
    python -m b3.esteira screen --family E-001  # one family
    python -m b3.esteira status                 # families, survivors, trial count

Results: research/b3/esteira/ (runs/<run>.json, ledger.jsonl, selected.json, trades/).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import itertools
import json
import math
import sys
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from b3 import pattern_search as ps
from b3.calendar import SP_TZ

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "b3" / "config" / "esteira_b3.json"
FAMILY_DIR = ROOT / "b3" / "families"
OUT = ROOT / "research" / "b3" / "esteira"
MIN_NS = 60 * 10**9


def load_config(path: Path = CONFIG) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise SystemExit(f"{path} is not approved by the owner: nothing is read")
    if cfg.get("split") != "exploration":
        raise SystemExit("the conveyor reads exploration only")
    return cfg


# ---------------------------------------------------------------------------------------------
# Families
# ---------------------------------------------------------------------------------------------

@dataclass
class Family:
    id: str                                   # "E-001"; never reused for a changed idea
    title: str
    hypothesis: str                           # why it should work, in one or two sentences
    grid: dict                                # {"param": [values]}, at most 3 params
    signal: Callable                          # signal(ctx, params) -> array of +1/-1/0
    timeframes: tuple = (1, 5)
    markets: tuple = ("WIN", "WDO")
    source: str = ""                          # where the idea came from (paper, article, own)
    author: str = ""

    def variants(self) -> list[dict]:
        keys = list(self.grid)
        return [dict(zip(keys, combo)) for combo in itertools.product(*[self.grid[k] for k in keys])] if keys else [{}]

    @property
    def code_hash(self) -> str:
        try:
            src = inspect.getsource(self.signal)
        except (OSError, TypeError):
            src = repr(self.signal)
        return hashlib.sha256((src + json.dumps(self.grid, sort_keys=True, default=str)).encode()).hexdigest()[:12]


def validate_family(f: Family, cfg: dict) -> list[str]:
    lim = cfg["family_limits"]
    why = []
    if not f.id or not f.title or not f.hypothesis:
        why.append("id, title and hypothesis are required")
    if len(f.grid) > lim["max_params"]:
        why.append(f"{len(f.grid)} parameters (max {lim['max_params']})")
    for k, v in f.grid.items():
        if not isinstance(v, (list, tuple)) or not v:
            why.append(f"grid[{k}] must be a non-empty list")
        elif len(v) > lim["max_values_per_param"]:
            why.append(f"grid[{k}] has {len(v)} values (max {lim['max_values_per_param']})")
    if len(f.variants()) > lim["max_variants_per_timeframe"]:
        why.append(f"{len(f.variants())} variants per timeframe (max {lim['max_variants_per_timeframe']})")
    bad_tf = [t for t in f.timeframes if t not in cfg["timeframes_min"]]
    if bad_tf:
        why.append(f"timeframes {bad_tf} not allowed (only {cfg['timeframes_min']})")
    bad_m = [m for m in f.markets if m not in cfg["markets"]]
    if bad_m:
        why.append(f"markets {bad_m} not allowed")
    return why


def load_families(directory: Path = FAMILY_DIR) -> list[Family]:
    out, seen = [], {}
    for path in sorted(Path(directory).glob("*.py")):
        if path.name.startswith("_"):
            continue
        name = f"b3_families_{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        for f in getattr(mod, "FAMILIES", []):
            if f.id in seen:
                raise ValueError(f"family id {f.id} defined twice ({seen[f.id]} and {path.name})")
            seen[f.id] = path.name
            out.append(f)
    return out


# ---------------------------------------------------------------------------------------------
# What a family sees
# ---------------------------------------------------------------------------------------------

class Ctx:
    """Bars + session features + causal helpers. Every helper at bar t uses bars <= t only."""

    def __init__(self, fr: ps.Frame) -> None:
        self.fr, self.df, self.tf = fr, fr.df, fr.tf
        self.day = fr.day                         # session index 0, 1, 2...
        self.o = fr.df["open"].to_numpy(float)
        self.h = fr.df["high"].to_numpy(float)
        self.l = fr.df["low"].to_numpy(float)
        self.c = fr.df["close"].to_numpy(float)
        self.v = fr.df["volume"].to_numpy(float)
        self.minute = fr.df["minute_of_day"].to_numpy()        # minutes since midnight (SP) at the bar's OPEN
        self.bar_in_day = fr.df["bar_in_day"].to_numpy()
        self.day_open = fr.df["day_open"].to_numpy(float)
        self.minutes_to_close = fr.df["minutes_to_close"].to_numpy(float)
        self.n = len(self.c)
        self._cache: dict = {}

    def cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def bars(self, minutes: float) -> int:
        """Number of bars in `minutes` at this timeframe (at least 1)."""
        return max(1, int(round(minutes / self.tf)))

    def prev(self, x: np.ndarray, lag: int = 1) -> np.ndarray:
        """x of `lag` bars earlier in the same session (NaN before)."""
        return ps._prev_in_day(np.asarray(x, float), self.day, lag)

    def cross(self, cond: np.ndarray) -> np.ndarray:
        """True on the bar where `cond` becomes true (it was false on the previous bar of the session)."""
        return ps._cross(np.asarray(cond, bool), self.day)

    def roll(self, x: np.ndarray, n: int, how: str = "mean", include_current: bool = True) -> np.ndarray:
        """Rolling statistic over n bars inside the session (NaN until n bars exist)."""
        s = pd.Series(np.asarray(x, float))
        g = s.groupby(self.day)
        f = {"mean": lambda z: z.rolling(n, min_periods=n).mean(), "max": lambda z: z.rolling(n, min_periods=n).max(),
             "min": lambda z: z.rolling(n, min_periods=n).min(), "std": lambda z: z.rolling(n, min_periods=n).std(ddof=0),
             "sum": lambda z: z.rolling(n, min_periods=n).sum()}[how]
        out = g.transform(lambda z: f(z if include_current else z.shift(1)))
        return out.to_numpy()

    def ema(self, x: np.ndarray, span: int) -> np.ndarray:
        """Exponential mean inside the session (NaN for the first `span` bars)."""
        s = pd.Series(np.asarray(x, float))
        return s.groupby(self.day).transform(lambda z: z.ewm(span=span, adjust=False, min_periods=span).mean()).to_numpy()

    def session_high(self, include_current: bool = False) -> np.ndarray:
        g = pd.Series(self.h).groupby(self.day)
        return (g.cummax() if include_current else g.transform(lambda z: z.cummax().shift(1))).to_numpy()

    def session_low(self, include_current: bool = False) -> np.ndarray:
        g = pd.Series(self.l).groupby(self.day)
        return (g.cummin() if include_current else g.transform(lambda z: z.cummin().shift(1))).to_numpy()

    def vwap(self) -> np.ndarray:
        return self.cached("vwap", lambda: ps._vwap(self.df))

    def rsi(self, n: int = 14) -> np.ndarray:
        return self.cached(("rsi", n), lambda: ps._rsi(self.df, n))

    def prev_sessions(self, values: np.ndarray, how: str = "mean", n: int = 20) -> np.ndarray:
        """mean/sd of `values` over every bar of the n sessions BEFORE this bar's session."""
        return ps._prev_sessions_stat(np.asarray(values, float), self.day, how, n)

    def same_minute(self, values: np.ndarray, how: str = "median", n: int = 20) -> np.ndarray:
        """median/mean of `values` at the same minute of day over the n sessions before."""
        return ps._same_minute_stat(np.asarray(values, float), self.day, self.minute, how, n)

    def prev_session_value(self, what: str) -> np.ndarray:
        """The previous session's 'high', 'low', 'close' or 'open' on every bar (NaN on the first session)."""
        col = {"high": self.h, "low": self.l, "close": self.c, "open": self.o}[what]
        agg = {"high": "max", "low": "min", "close": "last", "open": "first"}[what]
        per = pd.Series(col).groupby(self.day).agg(agg)
        per = per.reindex(range(int(self.day.max()) + 1)).shift(1)
        return per.to_numpy()[self.day]

    def other_close(self) -> np.ndarray:
        """The OTHER market's close on the same bar (WDO for WIN, WIN for WDO; NaN where missing)."""
        return self.df["wdo_close"].to_numpy(float)


def directions(f: Family, fr: ps.Frame, p: dict, warmup_sessions: int = 20, ctx: Ctx | None = None) -> np.ndarray:
    d = np.asarray(f.signal(ctx if ctx is not None and ctx.fr is fr else Ctx(fr), p))
    if d.shape != (len(fr.df),):
        raise ValueError(f"{f.id}: signal returned shape {d.shape}, expected ({len(fr.df)},)")
    d = np.nan_to_num(d.astype(float), nan=0.0)
    if not np.isin(d, (-1.0, 0.0, 1.0)).all():
        raise ValueError(f"{f.id}: signal must be +1, -1 or 0")
    d = np.where(fr.day >= warmup_sessions, d, 0.0)
    return d.astype(np.int8)


def sub_frame(fr: ps.Frame, lo: int, hi: int) -> ps.Frame:
    df = fr.df.iloc[lo:hi].reset_index(drop=True)
    day = fr.day[lo:hi] - fr.day[lo]
    return ps.Frame(fr.tf, df, fr.rules, fr.cal, day, fr.now[lo:hi], fr.entry_ok[lo:hi], fr.flatten[lo:hi],
                    fr.next_open_ok[lo:hi].copy())


def check_family(f: Family, fr: ps.Frame, cuts: int = 3, window_sessions: int = 21, seed: int = 7) -> list[str]:
    """Look-ahead and live-window checks on the first grid point. Returns the problems found (empty = ok)."""
    p = f.variants()[0]
    full = directions(f, fr, p)
    problems = []
    rng = np.random.default_rng(seed)
    n_days = int(fr.day.max()) + 1
    first_bar = {int(d): int(i) for d, i in zip(*np.unique(fr.day, return_index=True))}
    for _ in range(cuts):
        d = int(rng.integers(window_sessions + 1, n_days - 1))
        bars = np.flatnonzero(fr.day == d)
        cut = int(bars[len(bars) // 2])          # mid-session
        pre = directions(f, sub_frame(fr, 0, cut + 1), p)
        if not np.array_equal(pre, full[:cut + 1]):
            k = int(np.flatnonzero(pre != full[:cut + 1])[0])
            problems.append(f"look-ahead: the signal at bar {k} changes when later bars are removed (cut {cut})")
            break
        lo = first_bar[d - (window_sessions - 1)]    # `window_sessions` sessions: d and the 20 before
        win = directions(f, sub_frame(fr, lo, int(bars[-1]) + 1), p, warmup_sessions=window_sessions - 1)
        tail = win[-len(bars):]
        if not np.array_equal(tail, full[bars]):
            problems.append(f"window: session {d} needs more than {window_sessions - 1} earlier sessions")
            break
    return problems


# ---------------------------------------------------------------------------------------------
# Default exit replayed on 1-minute bars (vectorised)
# ---------------------------------------------------------------------------------------------

@dataclass
class Minutes:
    time: np.ndarray        # bar start, ns UTC
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    day: np.ndarray         # session date ordinal
    cut: np.ndarray         # per minute: the session's flatten time (ns)
    pos: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.pos:
            self.pos = {int(t): i for i, t in enumerate(self.time)}


def load_minutes(root: str, rules, cal, end: pd.Timestamp) -> Minutes:
    from b3.exit_study import minute_path
    m = minute_path(root, "back_adjusted", rules)
    m = m[m["time"] < end].reset_index(drop=True)
    t = m["time"].dt.as_unit("ns").astype("int64").to_numpy()
    local = m["time"].dt.tz_convert(SP_TZ).dt.date
    flat = {}
    for d in local.unique():
        s = cal.session(d)
        flat[d] = pd.Timestamp(s.flatten_at).value if s is not None else -1
    return Minutes(t, m["open"].to_numpy(float), m["high"].to_numpy(float), m["low"].to_numpy(float),
                   m["close"].to_numpy(float), np.array([d.toordinal() for d in local]),
                   np.array([flat[d] for d in local], dtype=np.int64))


def grid_points(brl: float, point_value: float, tick: float) -> float:
    return math.ceil(brl / point_value / tick - 1e-9) * tick


def simulate(entry_ns: np.ndarray, side: np.ndarray, mins: Minutes, ex: dict, inst, cost: dict,
             max_per_day: int) -> pd.DataFrame:
    """Trades of a signal list (entry time = signal bar close, side +1/-1) with the default exit.

    One position at a time: a signal while a position is open (entry < previous exit) is skipped."""
    tick, pv = inst.tick_size, inst.point_value_brl
    slip = cost["slippage_ticks_per_side"] * tick
    stop_slip = (cost["slippage_ticks_per_side"] + cost.get("stop_extra_ticks", 0.0)) * tick
    fees = 2 * cost["fees_per_side_brl"]
    H = int(ex["max_hold_min"])
    tgt_pts = grid_points(ex["target_brl"], pv, tick)
    stp_pts = grid_points(ex["stop_brl"], pv, tick)
    cols = ["entry_ns", "exit_ns", "side", "entry", "exit", "reason", "net_brl", "day"]
    i0 = np.array([mins.pos.get(int(t), -1) for t in entry_ns], dtype=np.int64)
    keep = i0 >= 0
    entry_ns, side, i0 = np.asarray(entry_ns)[keep], np.asarray(side)[keep].astype(int), i0[keep]
    if not len(i0):
        return pd.DataFrame(columns=cols)
    n = len(mins.time)
    idx = i0[:, None] + np.arange(H + 1)[None, :]
    inside = idx < n
    idx = np.minimum(idx, n - 1)
    t = mins.time[idx]
    cut_time = np.minimum(entry_ns + H * MIN_NS, mins.cut[i0])
    valid = inside & (mins.day[idx] == mins.day[i0][:, None]) & (t < cut_time[:, None])
    valid[:, 0] = valid[:, 0] & (mins.time[i0] < cut_time)
    # the window ends at the first invalid minute (time limit, flatten, end of session)
    end_j = np.where((~valid).any(axis=1), np.argmax(~valid, axis=1), H)
    E = mins.open[i0]
    s = side[:, None]
    stop = (E - side * stp_pts)[:, None]
    target = (E + side * tgt_pts)[:, None]
    lo, hi, op = mins.low[idx], mins.high[idx], mins.open[idx]
    stop_hit = np.where(s > 0, lo <= stop, hi >= stop) & valid
    tgt_hit = np.where(s > 0, hi >= target + tick, lo <= target - tick) & valid
    big = H + 10
    first_stop = np.where(stop_hit.any(axis=1), np.argmax(stop_hit, axis=1), big)
    first_tgt = np.where(tgt_hit.any(axis=1), np.argmax(tgt_hit, axis=1), big)
    rows = np.arange(len(i0))
    is_stop = (first_stop <= first_tgt) & (first_stop < big)
    is_tgt = ~is_stop & (first_tgt < big)
    X = np.empty(len(i0))
    xt = np.empty(len(i0), dtype=np.int64)
    reason = np.empty(len(i0), dtype=object)
    js = np.minimum(first_stop, H)
    o_s = op[rows, js]
    px_stop = np.where(side > 0, np.minimum(o_s, stop[:, 0]), np.maximum(o_s, stop[:, 0])) - side * stop_slip
    X[is_stop] = px_stop[is_stop]
    xt[is_stop] = t[rows, js][is_stop] + MIN_NS
    reason[is_stop] = "stop"
    jt = np.minimum(first_tgt, H)
    X[is_tgt] = target[:, 0][is_tgt]
    xt[is_tgt] = t[rows, jt][is_tgt] + MIN_NS
    reason[is_tgt] = "target"
    rest = ~is_stop & ~is_tgt
    # exit at the open of the first minute past the window if it is in the same session, else the last close
    je = np.minimum(end_j, H)
    nxt_ok = inside[rows, je] & (mins.day[idx[rows, je]] == mins.day[i0]) & (je > 0)
    last = np.maximum(je - 1, 0)
    px_end = np.where(nxt_ok, op[rows, je], mins.close[idx[rows, last]]) - side * slip
    t_end = np.where(nxt_ok, t[rows, je], t[rows, last] + MIN_NS)
    timed = entry_ns + H * MIN_NS <= mins.cut[i0]
    X[rest] = px_end[rest]
    xt[rest] = t_end[rest]
    reason[rest] = np.where(timed[rest], "time", "flatten")
    Eslip = E + side * slip
    net = (X - Eslip) * side * pv - fees
    # one position at a time, at most max_per_day entries per session
    order = np.argsort(entry_ns, kind="stable")
    take = np.zeros(len(i0), dtype=bool)
    free_at, per_day = -1, {}
    dd = mins.day[i0]
    for k in order:
        if entry_ns[k] < free_at or per_day.get(dd[k], 0) >= max_per_day:
            continue
        take[k] = True
        free_at = xt[k]
        per_day[dd[k]] = per_day.get(dd[k], 0) + 1
    out = pd.DataFrame({"entry_ns": entry_ns, "exit_ns": xt, "side": side, "entry": Eslip, "exit": X,
                        "reason": reason, "net_brl": net, "day": dd})
    return out[take].sort_values("entry_ns").reset_index(drop=True)


def signal_entries(fr: ps.Frame, d: np.ndarray, start: pd.Timestamp) -> tuple[np.ndarray, np.ndarray]:
    k = np.flatnonzero((d != 0) & fr.entry_ok & (fr.now >= start.value))
    return fr.now[k], d[k].astype(int)


# ---------------------------------------------------------------------------------------------
# Metrics and screen
# ---------------------------------------------------------------------------------------------

def metrics(t: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, slices: int) -> dict:
    years = (end - start).total_seconds() / (365.25 * 86400)
    if not len(t):
        return {"trades": 0, "trades_per_year": 0.0, "mean_net_brl": None, "positive_slices": 0}
    edges = np.linspace(start.value, end.value, slices + 1)
    sl = np.clip(np.searchsorted(edges, t["entry_ns"].to_numpy(), side="right") - 1, 0, slices - 1)
    by_slice = pd.Series(t["net_brl"].to_numpy()).groupby(sl).sum().reindex(range(slices), fill_value=0.0)
    return {"trades": int(len(t)), "trades_per_year": len(t) / years, "mean_net_brl": float(t["net_brl"].mean()),
            "total_net_brl": float(t["net_brl"].sum()), "hit_rate": float((t["net_brl"] > 0).mean()),
            "positive_slices": int((by_slice > 0).sum()), "by_slice_brl": [round(float(x), 2) for x in by_slice],
            "exit_reasons": t["reason"].value_counts().to_dict()}


def neighbours(grid: dict, p: dict) -> list[dict]:
    out = []
    for k, vals in grid.items():
        vals = list(vals)
        i = vals.index(p[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(vals):
                out.append(dict(p, **{k: vals[j]}))
    return out


def vkey(fid: str, market: str, tf: int, p: dict) -> str:
    return f"{fid}|{market}|{tf}m|" + ",".join(f"{k}={v}" for k, v in p.items())


def screen_family_rows(rows: list[dict], grid: dict, sc: dict) -> list[dict]:
    """Applies the screen to one family's rows on one market (rows carry 'tf', 'params', 'measured')."""
    by = {(r["tf"], json.dumps(r["params"], sort_keys=True, default=str)): r for r in rows}
    for r in rows:
        m = r["measured"]
        fails = []
        if m["trades_per_year"] < sc["min_trades_per_year"]:
            fails.append("trades_per_year")
        if m["mean_net_brl"] is None or not m["mean_net_brl"] > sc["mean_net_brl_measured_gt"]:
            fails.append("mean_net_measured")
        if m["positive_slices"] < sc["min_positive_slices"]:
            fails.append("positive_slices")
        nb = [by.get((r["tf"], json.dumps(q, sort_keys=True, default=str))) for q in neighbours(grid, r["params"])]
        nb = [x for x in nb if x is not None]
        pos = [x for x in nb if x["measured"]["mean_net_brl"] is not None and x["measured"]["mean_net_brl"] > 0]
        r["neighbours"] = len(nb)
        r["positive_neighbour_share"] = len(pos) / len(nb) if nb else 0.0
        if not nb or r["positive_neighbour_share"] < sc["plateau_min_positive_neighbour_share"]:
            fails.append("plateau")
        r["fails"] = fails
        r["passed_screen"] = not fails
    return rows


def overlap(a: pd.DataFrame, b: pd.DataFrame, tol_min: int = 5) -> float:
    """Share of a's trades with a same-side entry of b within tol_min minutes."""
    if not len(a) or not len(b):
        return 0.0
    hit = 0
    for sd in (1, -1):
        ea = np.sort(a.loc[a["side"] == sd, "entry_ns"].to_numpy())
        eb = np.sort(b.loc[b["side"] == sd, "entry_ns"].to_numpy())
        if not len(ea) or not len(eb):
            continue
        k = np.searchsorted(eb, ea)
        left = np.abs(ea - eb[np.clip(k - 1, 0, len(eb) - 1)])
        right = np.abs(eb[np.clip(k, 0, len(eb) - 1)] - ea)
        hit += int((np.minimum(left, right) <= tol_min * MIN_NS).sum())
    return hit / len(a)


# ---------------------------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def screened_ids() -> dict:
    p = OUT / "families.jsonl"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["family"]] = r
    return out


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _selected() -> list[dict]:
    p = OUT / "selected.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def costs_for(m: str) -> dict:
    c = ps.load_config()
    src = c["cost_reevaluation"] if m == "WIN" else c["wdo_extension"]["costs"]
    return {"measured": src["measured"], "measured_p90": src["measured_p90"]}


def screen(only: list[str] | None = None, cfg: dict | None = None) -> Path:
    from b3.markets import market
    cfg = cfg or load_config()
    fams = load_families()
    done = screened_ids()
    todo = [f for f in fams if (only is None or f.id in only) and f.id not in done]
    if not todo:
        raise SystemExit("no family left to screen (each id is screened once; a changed idea needs a new id)")
    today = datetime.now(SP_TZ).date()
    today_n = sum(1 for r in done.values()
                  if datetime.fromisoformat(r["screened_at_utc"]).astimezone(SP_TZ).date() == today)
    room = cfg["limits"]["max_families_per_day"] - today_n
    if room <= 0:
        raise SystemExit(f"daily limit reached ({cfg['limits']['max_families_per_day']} families)")
    todo = todo[:room]
    ps_cfg = ps.load_config()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sc, ex = cfg["screen"], cfg["default_exit"]
    report = {"run": run_id, "generated_at_utc": _now(), "config": "b3/config/esteira_b3.json", "split": "exploration",
              "default_exit": ex, "families": {}, "selected": []}
    selected = _selected()
    trades_dir = OUT / "trades"
    t0 = time.time()
    for mk in cfg["markets"]:
        fams_m = [f for f in todo if mk in f.markets]
        if not fams_m:
            continue
        ps.set_market(mk)
        start, end = ps.split_bounds("exploration")
        inst = market(mk).instrument()
        cst = costs_for(mk)
        frames, mins = {}, None
        for f in fams_m:
            prob = validate_family(f, cfg)
            entry = report["families"].setdefault(f.id, {"title": f.title, "hypothesis": f.hypothesis,
                                                          "code_hash": f.code_hash, "markets": {}})
            if prob:
                entry["rejected"] = prob
                continue
            rows = []
            for tf in f.timeframes:
                if tf not in frames:
                    frames[tf] = ps.load_frame(tf, end, ps_cfg)
                fr = frames[tf]
                if mins is None:
                    mins = load_minutes(mk, fr.rules, fr.cal, end)
                chk = check_family(f, fr, cfg["checks"]["causality_cuts"], cfg["checks"]["window_sessions"])
                if chk:
                    entry["markets"].setdefault(mk, {})[f"{tf}m_check"] = chk
                    continue
                ctx = Ctx(fr)
                for p in f.variants():
                    d = directions(f, fr, p, ctx=ctx)
                    e_ns, side = signal_entries(fr, d, start)
                    tm = simulate(e_ns, side, mins, ex, inst, cst["measured"], cfg["max_entries_per_session"])
                    tp = simulate(e_ns, side, mins, ex, inst, cst["measured_p90"], cfg["max_entries_per_session"])
                    key = vkey(f.id, mk, tf, p)
                    rows.append({"variant": key, "tf": tf, "params": p,
                                 "measured": metrics(tm, start, end, sc["time_slices"]),
                                 "measured_p90": {k: v for k, v in metrics(tp, start, end, sc["time_slices"]).items()
                                                  if k in ("trades", "mean_net_brl", "hit_rate")},
                                 "_trades": tm})
                    _append(OUT / "ledger.jsonl", {"variant": key, "run": run_id, "split": "exploration",
                                                   "read_at_utc": _now(), "trades": int(len(tm))})
            rows = screen_family_rows(rows, f.grid, sc)
            passing = sorted([r for r in rows if r["passed_screen"]], key=lambda r: -r["measured"]["mean_net_brl"])
            pick = None
            for r in passing:
                ov = max([overlap(r["_trades"], pd.read_csv(trades_dir / s["trades_file"]))
                          for s in selected if s["market"] == mk] or [0.0])
                r["max_overlap"] = ov
                if ov <= sc["max_overlap_with_selected"]:
                    pick = r
                    break
                r["fails"].append("same_bet_as_selected")
            if pick is not None:
                fn = hashlib.sha1(pick["variant"].encode()).hexdigest()[:12] + ".csv.gz"
                trades_dir.mkdir(parents=True, exist_ok=True)
                pick["_trades"].to_csv(trades_dir / fn, index=False)
                sel = {"variant": pick["variant"], "family": f.id, "market": mk, "tf": pick["tf"], "params": pick["params"],
                       "code_hash": f.code_hash, "measured": {k: v for k, v in pick["measured"].items() if k != "by_slice_brl"},
                       "selected_at_utc": _now(), "run": run_id, "trades_file": fn, "status": "awaiting_demo"}
                selected.append(sel)
                report["selected"].append(sel["variant"])
            for r in rows:
                r.pop("_trades", None)
            rows.sort(key=lambda r: -(r["measured"]["mean_net_brl"] if r["measured"]["mean_net_brl"] is not None else -1e9))
            entry["markets"].setdefault(mk, {}).update({"variants": len(rows), "passed_screen": len(passing),
                                                        "selected": pick["variant"] if pick else None, "rows": rows})
            print(f"{f.id} {mk}: {len(rows)} variants, {len(passing)} pass the screen, "
                  f"selected {pick['variant'] if pick else '-'} ({time.time() - t0:.0f}s)", flush=True)
    for f in todo:
        _append(OUT / "families.jsonl", {"family": f.id, "title": f.title, "code_hash": f.code_hash, "run": run_id,
                                         "screened_at_utc": _now(), "author": f.author,
                                         "rejected": report["families"].get(f.id, {}).get("rejected")})
    n_trials = sum(1 for line in (OUT / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()) \
        if (OUT / "ledger.jsonl").exists() else 0
    report["conveyor_trials_so_far"] = n_trials
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "selected.json").write_text(json.dumps(selected, indent=1, default=str), encoding="utf-8")
    path = OUT / "runs" / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    ps.set_market("WIN")
    return path


def status() -> dict:
    done = screened_ids()
    sel = _selected()
    ledger = OUT / "ledger.jsonl"
    n = sum(1 for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()) if ledger.exists() else 0
    return {"families_screened": len(done), "variants_read": n, "selected": sel,
            "waiting": [f.id for f in load_families() if f.id not in done]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.esteira")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("screen")
    s.add_argument("--family", action="append")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "screen":
        print(screen(a.family))
    else:
        print(json.dumps(status(), indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
