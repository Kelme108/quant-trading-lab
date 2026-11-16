"""Order-flow (aggressor side) search on the recorded WIN/WDO ticks, pre-registered in b3/config/tick_program_b3.json
(owner 2026-11-16: splits approved, "queremos estrategias rapidas") before any read.

Builds 1-minute bars from the trades of the ACTIVE contract of each day (b3/data/tick_recorder.py files), with the
aggressor volumes, then runs the 32 signal settings x 2 timeframes x 6 exits through the fast simulator of
b3/pattern_search.py (same fill rules as b3/backtest.py) at the measured costs.

    python -m b3.tick_search bars  --market WIN          # build/refresh the tick bars (no strategy read)
    python -m b3.tick_search explore --market WIN        # read exploration (interim before 2027-01-01)

Results: research/b3/ticks/; trials: research/b3/ticks/ledger.jsonl. Validation and final test are not readable
from here: validation gets its own command after the end-of-exploration read names the finalists.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3 import b3_data
from b3 import pattern_search as ps
from b3.calendar import Holidays, SessionRules, UnknownCalendarYear
from b3.contracts import active_contract
from b3.data.tick_recorder import OUT as TICKS
from b3.strategy import session_features

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "b3" / "config" / "tick_program_b3.json"
OUT = ROOT / "research" / "b3" / "ticks"
BARS = ROOT / "user_data" / "data" / "b3" / "clear" / "tickbars"
LEDGER = OUT / "ledger.jsonl"
SERVER_OFFSET_S = 3 * 3600          # time_msc is B3 wall time counted as UTC; real UTC = + 3 h
LAST, BUY, SELL = 8, 32, 64


def load_config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("approved_by_owner") is not True:
        raise RuntimeError("tick_program_b3.json is not approved by the owner")
    return cfg


def split_days(cfg: dict, split: str) -> tuple[date, date]:
    s = cfg["splits"][split]
    if split == "final_test" and s.get("locked", True):
        raise PermissionError("the tick program's final test is locked (tick_program_b3.json)")
    end = date.fromisoformat(s["end_b3"]) if s["end_b3"] else date(2100, 1, 1)
    return date.fromisoformat(s["start_b3"]), end


# ---------------------------------------------------------------------------------------------
# Bars from ticks
# ---------------------------------------------------------------------------------------------

def _active(root: str, d: date, holidays: Holidays) -> str | None:
    """The active contract (b3/contracts.py). When the roll needs a year without the official B3 calendar (e.g. WDOF27
    from late November 2026 until B3 publishes 2027), the recorded contract of that root with the most trades that
    day - the same contract in practice, since the roll is the volume crossover. Engineering amendment of
    2026-11-16, after the first interim read, reported to the owner; it changes no day already read."""
    try:
        return active_contract(root, d, holidays).code
    except UnknownCalendarYear:
        best, most = None, -1
        for meta in TICKS.glob(f"{root}*/{d.isoformat()}.json"):
            try:
                n = json.loads(meta.read_text(encoding="utf-8")).get("trades", 0)
            except (OSError, ValueError):
                continue
            if n > most:
                best, most = meta.parent.name, n
        return best


def _read_trades(path: Path) -> pd.DataFrame:
    t = pd.read_csv(path, usecols=["time_msc", "last", "volume_real", "flags"])
    f = t["flags"].to_numpy(np.int64)
    t = t[((f & LAST) != 0) & (t["last"].to_numpy() > 0)]
    return t


def build_bars(root: str, start: date, end: date, log=print) -> pd.DataFrame:
    """1-minute bars of the active contract with aggressor volumes; 'big' trades use the 99th percentile of trade
    size over the 5 sessions before (tick_program_b3.json families T04/T05)."""
    holidays = Holidays.from_file()
    days, files = [], []
    d = start
    while d <= end:
        if d.weekday() < 5:
            code = _active(root, d, holidays)
            f = TICKS / code / f"{d.isoformat()}.csv.gz" if code else None
            if f is not None and f.exists():
                days.append(d)
                files.append(f)
        d += timedelta(days=1)
    sizes: list[Counter] = []
    for f in files:                                      # pass 1: trade-size distribution per day
        t = _read_trades(f)
        sizes.append(Counter(t["volume_real"].to_numpy().round(0).astype(int).tolist()))
    out = []
    for i, (d, f) in enumerate(zip(days, files)):        # pass 2: bars
        prev = Counter()
        for c in sizes[max(0, i - 5):i]:
            prev.update(c)
        thr = np.inf
        if i >= 5 and prev:
            ks = np.array(sorted(prev))
            cum = np.cumsum([prev[k] for k in ks]) / sum(prev.values())
            thr = float(ks[np.searchsorted(cum, 0.99)])
        t = _read_trades(f)
        if not len(t):                                   # a day recorded as absent (old day, nothing in the terminal)
            continue
        fl = t["flags"].to_numpy(np.int64)
        vol = t["volume_real"].to_numpy(float)
        buy = ((fl & BUY) != 0) & ((fl & SELL) == 0)
        sell = ((fl & SELL) != 0) & ((fl & BUY) == 0)
        big = vol >= thr
        g = pd.DataFrame({"m": t["time_msc"].to_numpy(np.int64) // 60_000, "p": t["last"].to_numpy(float), "v": vol,
                          "bv": np.where(buy, vol, 0.0), "sv": np.where(sell, vol, 0.0),
                          "bbv": np.where(buy & big, vol, 0.0), "bsv": np.where(sell & big, vol, 0.0)})
        a = g.groupby("m").agg(open=("p", "first"), high=("p", "max"), low=("p", "min"), close=("p", "last"),
                               volume=("v", "sum"), buy_vol=("bv", "sum"), sell_vol=("sv", "sum"),
                               big_buy=("bbv", "sum"), big_sell=("bsv", "sum"), n_trades=("p", "size"))
        a["contract"] = f.parent.name
        a["big_threshold"] = thr
        out.append(a)
        log(f"{root} {d} {f.parent.name}: {len(t)} trades, {len(a)} minutes, big >= {thr}")
    if not out:
        return pd.DataFrame()
    bars = pd.concat(out).reset_index()
    bars["time"] = pd.to_datetime(bars["m"] * 60 + SERVER_OFFSET_S, unit="s", utc=True)
    bars["tick_volume"] = bars["n_trades"]
    bars["spread"] = 0
    return bars.drop(columns="m")


def bars_path(root: str) -> Path:
    return BARS / f"{root}-1m.csv.gz"


def refresh_bars(root: str, cfg: dict) -> Path:
    start = date.fromisoformat(cfg["splits"]["exploration"]["start_b3"])
    end = datetime.now(timezone.utc).date()
    b = build_bars(root, start, end)
    BARS.mkdir(parents=True, exist_ok=True)
    b.to_csv(bars_path(root), index=False)
    return bars_path(root)


FLOW_COLS = ("buy_vol", "sell_vol", "big_buy", "big_sell", "n_trades")


def _resample(b: pd.DataFrame, tf: int) -> pd.DataFrame:
    if tf == 1:
        return b
    key = b["time"].dt.floor(f"{tf}min")
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "tick_volume": "sum",
           "spread": "max", **{c: "sum" for c in FLOW_COLS}}
    return b.groupby(key).agg(agg).reset_index()


def load_tick_frame(root: str, tf: int, end_day: date, cfg: dict) -> ps.Frame:
    """A pattern_search.Frame on the tick bars (session-only, complete days, up to end_day inclusive)."""
    raw = pd.read_csv(bars_path(root), parse_dates=["time"])
    raw["time"] = pd.to_datetime(raw["time"], utc=True)
    raw = raw[raw["time"].dt.tz_convert(ps.SP_TZ).dt.date <= end_day].reset_index(drop=True)
    raw = _resample(raw, tf)
    r = cfg_rules()
    cal0 = b3_data.history_calendar(root, raw, r)
    bars = b3_data.session_only_b3(raw, cal0, tf)
    skipped = b3_data.incomplete_days(bars, cal0, tf, 0.9)
    cal = b3_data.history_calendar(root, raw, r, skipped)
    local_day = bars["time"].dt.tz_convert(ps.SP_TZ).dt.date
    bars = bars[~local_day.isin(skipped)].reset_index(drop=True)
    df = session_features(bars, cal, tf)
    for c in FLOW_COLS:
        df[c] = bars[c].to_numpy(float)
    df["adj_offset"] = 0.0
    df["wdo_close"] = np.nan
    days = list(dict.fromkeys(df["local_date"]))
    di = {d: i for i, d in enumerate(days)}
    day = df["local_date"].map(di).to_numpy()
    times = df["time"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy().astype("datetime64[ns]").astype(np.int64)
    now = times + tf * 60 * 10**9
    sess = {d: cal.session(d) for d in days}
    es = np.array([pd.Timestamp(sess[d].entry_start).value for d in df["local_date"]])
    ee = np.array([pd.Timestamp(sess[d].entry_end).value for d in df["local_date"]])
    fl = np.array([pd.Timestamp(sess[d].flatten_at).value for d in df["local_date"]])
    nxt = np.zeros(len(df), dtype=bool)
    nxt[:-1] = (times[1:] == now[:-1]) & (day[1:] == day[:-1])
    return ps.Frame(tf, df, r, cal, day, now, (now >= es) & (now < ee), now >= fl, nxt)


def cfg_rules() -> SessionRules:
    r = ps.load_config()["data"]["session_rules"]        # the same session rules as the bar search
    return SessionRules(r["entry_start_after_open_min"], r["entry_end_before_close_min"], r["flatten_before_close_min"])


# ---------------------------------------------------------------------------------------------
# Signals (tick_program_b3.json families)
# ---------------------------------------------------------------------------------------------

def _roll_sum_in_day(x: np.ndarray, day: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).groupby(day).transform(lambda s: s.rolling(n, min_periods=n).sum()).to_numpy()


class TickSignals:
    WARMUP = 5

    def __init__(self, fr: ps.Frame) -> None:
        self.fr, self.df, self.day = fr, fr.df, fr.day
        self.c = fr.df["close"].to_numpy(float)
        self.minute = fr.df["minute_of_day"].to_numpy()
        self.bv = fr.df["buy_vol"].to_numpy(float)
        self.sv = fr.df["sell_vol"].to_numpy(float)
        self._cache: dict = {}
        self.has_history = self.day >= self.WARMUP

    def _get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def bars(self, minutes) -> int:
        return max(1, int(round(minutes / self.fr.tf)))

    def direction(self, fam: str, p: dict) -> np.ndarray:
        d = getattr(self, "_" + fam.split("_", 1)[0].lower())(fam, p)
        return np.where(self.has_history, d, 0).astype(np.int8)

    def _imb(self, m):
        def f():
            b = _roll_sum_in_day(self.bv, self.day, m)
            s = _roll_sum_in_day(self.sv, self.day, m)
            imb = (b - s) / np.where(b + s > 0, b + s, np.nan)
            sd = ps._prev_sessions_stat(imb, self.day, "sd", n=self.WARMUP)
            return imb / sd
        return self._get(("imb", m), f)

    def _ret(self, m):
        return self._get(("ret", m), lambda: ps._session_ret(self.c, self.day, m))

    def _t01(self, fam, p, sign=1):
        z = self._imb(self.bars(p["M"]))
        up = ps._cross(z >= p["k"], self.day)
        dn = ps._cross(z <= -p["k"], self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _t02(self, fam, p):
        return self._t01(fam, p, -1)

    def _t03(self, fam, p):
        m = self.bars(p["M"])
        z, r = self._imb(m), self._ret(m)
        short = ps._cross((z >= p["k"]) & (r <= 0), self.day)
        long = ps._cross((z <= -p["k"]) & (r >= 0), self.day)
        return long.astype(int) - short.astype(int)

    def _big(self, m):
        def f():
            nb = _roll_sum_in_day(self.df["big_buy"].to_numpy(float) - self.df["big_sell"].to_numpy(float), self.day, m)
            sd = ps._prev_sessions_stat(nb, self.day, "sd", n=self.WARMUP)
            return nb / np.where(sd > 0, sd, np.nan)
        return self._get(("big", m), f)

    def _t04(self, fam, p, sign=1):
        z = self._big(self.bars(p["M"]))
        up = ps._cross(z >= p["k"], self.day)
        dn = ps._cross(z <= -p["k"], self.day)
        return sign * (up.astype(int) - dn.astype(int))

    def _t05(self, fam, p):
        return self._t04(fam, p, -1)

    def _t06(self, fam, p):
        n = self.df["n_trades"].to_numpy(float)
        med = self._get("nmed", lambda: ps._same_minute_stat(n, self.day, self.minute, "median", n=self.WARMUP))
        burst = n >= p["k"] * med
        return np.where(burst, np.sign(self.bv - self.sv), 0).astype(int)


# ---------------------------------------------------------------------------------------------
# Exploration read
# ---------------------------------------------------------------------------------------------

def _log(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def positive_months_share(t: pd.DataFrame) -> float:
    if not len(t):
        return 0.0
    mo = pd.to_datetime(t["exit_ns"], utc=True).dt.tz_convert(ps.SP_TZ).dt.strftime("%Y-%m")
    by = t.groupby(mo)["net_pct"].sum()
    return float((by > 0).mean())


def gate(b: dict, c: dict, pm: float, dsr, pbo, g: dict) -> list[str]:
    f = []
    if b.get("trades_per_year", 0) < g["min_trades_per_year"]:
        f.append("trades_per_year")
    if b.get("net_return_pct", -1) <= g["net_measured_gt"]:
        f.append("net_measured")
    if c.get("net_return_pct", -1) <= g["net_measured_p90_gt"]:
        f.append("net_measured_p90")
    if b.get("net_without_best_pct", -1) <= g["net_without_best_trade_gt"]:
        f.append("net_without_best")
    if max(b.get("max_drawdown_pct", 100), c.get("max_drawdown_pct", 100)) > g["max_drawdown_pct"]:
        f.append("drawdown")
    if pm < g["positive_months_share"]:
        f.append("positive_months")
    if dsr is None or not dsr >= g["deflated_sharpe_min"]:
        f.append("deflated_sharpe")
    if pbo is None or pbo > g["pbo_max"]:
        f.append("pbo")
    return f


def explore(root: str, today: date | None = None) -> Path:
    from lab import stats
    cfg = load_config()
    today = today or datetime.now(timezone.utc).date()
    s0, s1 = split_days(cfg, "exploration")
    end_day = min(s1, today)
    interim = end_day < s1
    ps.set_market(root)
    pcfg = ps.load_config()
    cm, cp = ps.measured_cost("measured", pcfg), ps.measured_cost("measured_p90", pcfg)
    ex = cfg["execution"]
    rows, daily = [], {}
    sessions = None
    for tf in ex["timeframes_min"]:
        fr = load_tick_frame(root, tf, end_day, cfg)
        sig = TickSignals(fr)
        start = pd.Timestamp(fr.now[fr.day == sig.WARMUP][0] - tf * 60 * 10**9, unit="ns", tz="UTC")
        n_sess = int(fr.day.max()) + 1 - sig.WARMUP
        sessions = n_sess if sessions is None else min(sessions, n_sess)
        years = n_sess / 250.0
        for fam, p in ps.signal_settings({"families": cfg["families"]}):
            d = sig.direction(fam, p)
            for hold, stop in itertools.product(ex["exit_grid"]["hold_min"], ex["exit_grid"]["stop_frac"]):
                vid = ps.variant_id(fam, p, tf, hold, stop)
                tb = ps.simulate(fr, d, hold, stop, cm, 8, start)
                tc = ps.simulate(fr, d, hold, stop, cp, 8, start)
                daily[vid] = ps.daily_returns(tb, fr, start)
                mb, mc = ps.metrics(tb, fr, start, years), ps.metrics(tc, fr, start, years)
                rows.append({"variant": vid, "family": fam, "params": p, "tf": tf, "hold_min": hold, "stop_frac": stop,
                             "measured": mb, "measured_p90": mc, "positive_months_share": positive_months_share(tb)})
                _log({"variant": vid, "market": root, "split": "exploration", "interim": interim, "through": str(end_day),
                      "read_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "trades": mb.get("trades", 0)})
        print(f"{root} tf {tf}m: {n_sess} sessions after warmup", flush=True)
    mat = pd.DataFrame(daily).fillna(0.0)
    sharpes = [stats.sharpe(mat[k].to_numpy()) for k in mat.columns]
    var = float(np.var(sharpes, ddof=1))
    try:
        pbo = stats.pbo_cscv(mat.to_numpy(), n_slices=8)
    except (ValueError, ZeroDivisionError):              # fewer sessions than slices: no PBO yet, the gate fails
        pbo = None
    g = cfg["gate"]
    for r in rows:
        ds = stats.deflated_sharpe(mat[r["variant"]].to_numpy(), len(rows), var)
        r["deflated_sharpe"] = ds
        r["fails"] = gate(r["measured"], r["measured_p90"], r["positive_months_share"], ds["dsr"],
                          pbo["pbo"] if pbo else None, g)
        r["passed"] = not r["fails"]
    rows.sort(key=lambda r: -(r["deflated_sharpe"]["dsr"] if r["deflated_sharpe"]["dsr"] == r["deflated_sharpe"]["dsr"] else -1))
    out = {"market": root, "split": "exploration", "interim": interim, "through_b3_day": str(end_day),
           "_interim": "an interim read: the gate decision uses only the read after 2026-12-31 (tick_program_b3.json reads)" if interim else "",
           "sessions_after_warmup": sessions, "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "n_variants": len(rows), "variance_of_trial_sharpes": var, "pbo": pbo,
           "passed": [r["variant"] for r in rows if r["passed"]], "rows": rows}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{root}-exploration-{end_day.isoformat()}.json"
    path.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    mat.to_csv(OUT / f"{root}-exploration-{end_day.isoformat()}-daily.csv.gz")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.tick_search")
    ap.add_argument("cmd", choices=("bars", "explore"))
    ap.add_argument("--market", default="WIN", choices=("WIN", "WDO"))
    a = ap.parse_args(argv)
    cfg = load_config()
    if a.cmd == "bars":
        print(refresh_bars(a.market, cfg))
    else:
        print(explore(a.market))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
