"""Focused study of P-026 (b3/config/p026_lab.json, owner 2026-11-18): entry versions x exit versions on EXPLORATION,
each exit also run on random entries (same minute of day, random session, random side) as the control.

    python -m b3.p026_lab run            # both markets
    python -m b3.p026_lab run --market WIN

Results: research/b3/p026_lab/<run>.json. Validation is never read here.
"""

from __future__ import annotations

import argparse
import itertools
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from b3 import esteira as es
from b3 import pattern_search as ps

ROOT = es.ROOT
CONFIG = ROOT / "b3" / "config" / "p026_lab.json"
OUT = ROOT / "research" / "b3" / "p026_lab"
MIN_NS = es.MIN_NS


def load_config() -> dict:
    c = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not c.get("approved_by_owner") or c.get("split") != "exploration":
        raise SystemExit("p026_lab.json must be approved and on exploration")
    return c


def entry_points(cfg: dict, tf: int) -> list[dict]:
    g = cfg["entry_grid"]
    return [{"box_min": b, "ratio_max": r, "direction": d}
            for b, r, d in itertools.product(g["box_min"], g["ratio_max"], g["direction"])]


# ---------------------------------------------------------------------------------------------
# Entries (causal: everything at bar t uses bars <= t)
# ---------------------------------------------------------------------------------------------

def features(ctx: es.Ctx, box_min: int, tick: float) -> dict:
    """Per bar: box high/low before t, compression ratio vs the time-of-day norm, V (share of price)."""
    def build():
        n = ctx.bars(box_min)
        hi = ctx.roll(ctx.h, n, "max", include_current=False)
        lo = ctx.roll(ctx.l, n, "min", include_current=False)
        r = (hi - lo) / ctx.prev(ctx.c)
        norm = ctx.same_minute(r, "median")
        return {"hi": hi, "lo": lo, "ratio": r / norm}
    f = ctx.cached(("box", box_min), build)
    m = ctx.bars(30)
    v = ctx.cached("V", lambda: ctx.same_minute(np.abs(ctx.c / ctx.prev(ctx.c, m) - 1.0), "mean"))
    return f | {"V": v}


def directions(ctx: es.Ctx, p: dict, tick: float) -> np.ndarray:
    f = features(ctx, p["box_min"], tick)
    comp = f["ratio"] <= p["ratio_max"]
    ok = comp & (ctx.minutes_to_close >= 75)
    up = ok & (ctx.c >= f["hi"] + tick)
    dn = ok & (ctx.c <= f["lo"] - tick)
    d = up.astype(int) - dn.astype(int)
    return d if p["direction"] == "follow" else -d


# ---------------------------------------------------------------------------------------------
# Exits on 1-minute bars (vectorised; breakeven/trailing use the bars BEFORE the current minute)
# ---------------------------------------------------------------------------------------------

def _ceil_tick(x, tick):
    return np.ceil(np.asarray(x, float) / tick - 1e-9) * tick


def distances(spec: dict, E: np.ndarray, half_box: np.ndarray, mid: np.ndarray, Vp: np.ndarray, pv: float,
              tick: float) -> dict:
    def one(s):
        if s is None:
            return np.full(len(E), np.inf)
        kind, k = s[0], (s[1] if len(s) > 1 else None)
        if kind == "brl":
            d = np.full(len(E), k / pv)
        elif kind == "B":
            d = k * half_box
        elif kind == "V":
            d = k * Vp * E
        elif kind == "box_mid_clamped":
            d = np.clip(np.abs(E - mid), 0.001 * E, 0.003 * E)
        else:
            raise ValueError(kind)
        return np.maximum(_ceil_tick(d, tick), tick)
    return {"stop": one(spec["stop"]), "target": one(spec.get("target")), "be": one(spec.get("breakeven")),
            "trail": one(spec.get("trail"))}


def simulate(i0: np.ndarray, side: np.ndarray, entry_ns: np.ndarray, mins: es.Minutes, dist: dict, hold: int,
             inst, cost: dict, max_per_day: int) -> pd.DataFrame:
    tick, pv = inst.tick_size, inst.point_value_brl
    slip = cost["slippage_ticks_per_side"] * tick
    stop_slip = (cost["slippage_ticks_per_side"] + cost.get("stop_extra_ticks", 0.0)) * tick
    fees = 2 * cost["fees_per_side_brl"]
    cols = ["entry_ns", "exit_ns", "side", "entry", "exit", "reason", "net_brl", "gross_brl", "day"]
    if not len(i0):
        return pd.DataFrame(columns=cols)
    n, H = len(mins.time), hold
    idx = i0[:, None] + np.arange(H + 1)[None, :]
    inside = idx < n
    idx = np.minimum(idx, n - 1)
    t = mins.time[idx]
    cut_time = np.minimum(entry_ns + H * MIN_NS, mins.cut[i0])
    valid = inside & (mins.day[idx] == mins.day[i0][:, None]) & (t < cut_time[:, None])
    valid[:, 0] &= mins.time[i0] < cut_time
    end_j = np.where((~valid).any(axis=1), np.argmax(~valid, axis=1), H)
    s = side.astype(float)
    E = mins.open[i0]
    # long-like coordinates: x = s * price
    xh = np.where(s[:, None] > 0, mins.high[idx], -mins.low[idx])
    xl = np.where(s[:, None] > 0, mins.low[idx], -mins.high[idx])
    xo = s[:, None] * mins.open[idx]
    xE = (s * E)[:, None]
    best_prev = np.maximum.accumulate(np.where(valid, xh, -np.inf), axis=1)
    best_prev = np.concatenate([np.full((len(i0), 1), -np.inf), best_prev[:, :-1]], axis=1)
    stop_lvl = xE - dist["stop"][:, None]
    be_on = (best_prev - xE) >= dist["be"][:, None]
    stop_lvl = np.where(be_on, np.maximum(stop_lvl, xE), stop_lvl)
    stop_lvl = np.maximum(stop_lvl, best_prev - dist["trail"][:, None])
    tgt = xE + dist["target"][:, None]
    stop_hit = (xl <= stop_lvl) & valid
    tgt_hit = (xh >= tgt + tick) & valid
    big = H + 10
    fs = np.where(stop_hit.any(axis=1), np.argmax(stop_hit, axis=1), big)
    ft = np.where(tgt_hit.any(axis=1), np.argmax(tgt_hit, axis=1), big)
    rows = np.arange(len(i0))
    is_stop = (fs <= ft) & (fs < big)
    is_tgt = ~is_stop & (ft < big)
    X = np.empty(len(i0))
    xt = np.empty(len(i0), dtype=np.int64)
    reason = np.empty(len(i0), dtype=object)
    js = np.minimum(fs, H)
    lvl = stop_lvl[rows, js]
    px = np.minimum(xo[rows, js], lvl) - stop_slip                     # long-like fill
    X[is_stop] = (s * px)[is_stop]
    xt[is_stop] = t[rows, js][is_stop] + MIN_NS
    reason[is_stop] = np.where(lvl[is_stop] >= xE[is_stop, 0], "stop_be_trail", "stop")
    jt = np.minimum(ft, H)
    X[is_tgt] = (s * tgt[:, 0])[is_tgt]
    xt[is_tgt] = t[rows, jt][is_tgt] + MIN_NS
    reason[is_tgt] = "target"
    rest = ~is_stop & ~is_tgt
    je = np.minimum(end_j, H)
    nxt_ok = inside[rows, je] & (mins.day[idx[rows, je]] == mins.day[i0]) & (je > 0)
    last = np.maximum(je - 1, 0)
    px_end = np.where(nxt_ok, mins.open[idx[rows, je]], mins.close[idx[rows, last]]) - s * slip
    X[rest] = px_end[rest]
    xt[rest] = np.where(nxt_ok, t[rows, je], t[rows, last] + MIN_NS)[rest]
    reason[rest] = np.where((entry_ns + H * MIN_NS <= mins.cut[i0])[rest], "time", "flatten")
    Es = E + s * slip
    net = (X - Es) * s * pv - fees
    gross = (np.where(is_tgt, X, np.where(is_stop, X + s * stop_slip, X + s * slip)) - E) * s * pv
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
    out = pd.DataFrame({"entry_ns": entry_ns, "exit_ns": xt, "side": side, "entry": Es, "exit": X, "reason": reason,
                        "net_brl": net, "gross_brl": gross, "day": dd})
    return out[take].sort_values("entry_ns").reset_index(drop=True)


def randomise(i0: np.ndarray, mins: es.Minutes, start_ns: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Each entry moved to a random other exploration session at the same minute of day; random side."""
    mod = ((mins.time // MIN_NS) % 1440)
    key = mins.day * 1440 + mod
    pos = {int(k): i for i, k in enumerate(key)}
    days = np.unique(mins.day[mins.time >= start_ns])
    new = np.empty(len(i0), dtype=np.int64)
    for j, i in enumerate(i0):
        for _ in range(20):
            d = days[rng.integers(len(days))]
            k = pos.get(int(d * 1440 + mod[i]), -1)
            if k >= 0 and d != mins.day[i]:
                break
        new[j] = k
    side = rng.choice([-1, 1], len(i0))
    keep = new >= 0
    return new[keep], side[keep], keep


def summary(t: pd.DataFrame, start, end, slices: int) -> dict:
    m = es.metrics(t, start, end, slices)
    m.pop("by_slice_brl", None)
    if len(t):
        m["mean_gross_brl"] = float(t["gross_brl"].mean())
        m["net_per_year_brl"] = m["total_net_brl"] / ((end - start).total_seconds() / (365.25 * 86400))
    return m


# ---------------------------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------------------------

def run(markets: list[str] | None = None) -> Path:
    from b3.markets import market
    cfg = load_config()
    sel = cfg["selection"]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {"run": run_id, "config": "b3/config/p026_lab.json", "split": "exploration", "rows": [], "checks": {}}
    ps_cfg = ps.load_config()
    t0 = time.time()
    for mk in markets or cfg["markets"]:
        ps.set_market(mk)
        start, end = ps.split_bounds("exploration")
        inst = market(mk).instrument()
        cost = es.costs_for(mk)
        tick, pv = inst.tick_size, inst.point_value_brl
        mins = None
        for tf in cfg["entry_grid"]["tf"]:
            fr = ps.load_frame(tf, end, ps_cfg)
            if mins is None:
                mins = es.load_minutes(mk, fr.rules, fr.cal, end)
            ctx = es.Ctx(fr)
            for p in entry_points(cfg, tf):
                fam = es.Family("P026", "p", "h", {"x": [1]}, lambda c, _q, p=p: directions(c, p, tick))
                chk = es.check_family(fam, fr, 3, 21)
                report["checks"][f"{mk}|{tf}m|{json.dumps(p)}"] = chk
                if chk:
                    print(mk, tf, p, "CHECK FAILED", chk, flush=True)
                    continue
                d = es.directions(fam, fr, {"x": 1}, ctx=ctx)
                k = np.flatnonzero((d != 0) & fr.entry_ok & (fr.now >= start.value))
                f = features(ctx, p["box_min"], tick)
                e_ns, side = fr.now[k], d[k].astype(int)
                i0 = np.array([mins.pos.get(int(x), -1) for x in e_ns], dtype=np.int64)
                ok = i0 >= 0
                e_ns, side, i0 = e_ns[ok], side[ok], i0[ok]
                hb = ((f["hi"] - f["lo"]) / 2)[k][ok]
                mid = ((f["hi"] + f["lo"]) / 2)[k][ok]
                Vp = f["V"][k][ok]
                good = np.isfinite(hb) & np.isfinite(Vp) & (hb > 0) & (Vp > 0)
                e_ns, side, i0, hb, mid, Vp = e_ns[good], side[good], i0[good], hb[good], mid[good], Vp[good]
                E = mins.open[i0]
                rng = np.random.default_rng(26)
                rand = [randomise(i0, mins, start.value, rng) for _ in range(cfg["random_control"]["seeds"])]
                for ex_id, spec in cfg["exits"].items():
                    dist = distances(spec, E, hb, mid, Vp, pv, tick)
                    tm = simulate(i0, side, e_ns, mins, dist, spec["hold_min"], inst, cost["measured"], 4)
                    tp = simulate(i0, side, e_ns, mins, dist, spec["hold_min"], inst, cost["measured_p90"], 4)
                    rnd = []
                    for ri, rs, keep in rand:
                        dr = {kk: vv[keep] for kk, vv in dist.items()}
                        tr = simulate(ri, rs, mins.time[ri], mins, dr, spec["hold_min"], inst, cost["measured"], 4)
                        rnd.append(float(tr["net_brl"].mean()) if len(tr) else 0.0)
                    row = {"market": mk, "tf": tf, "entry": p, "exit": ex_id,
                           "measured": summary(tm, start, end, cfg["selection"]["time_slices"]),
                           "measured_p90_mean_net_brl": float(tp["net_brl"].mean()) if len(tp) else None,
                           "random_mean_net_brl": float(np.mean(rnd)), "random_runs": rnd}
                    report["rows"].append(row)
                print(f"{mk} {tf}m {p} done ({time.time() - t0:.0f}s)", flush=True)
    ps.set_market("WIN")
    report["rows"] = select(report["rows"], cfg)
    report["n_versions_read"] = len(report["rows"])
    picks = [r for r in report["rows"] if r.get("candidate")]
    report["picked"] = {mk: max([r for r in picks if r["market"] == mk], key=lambda r: r["measured"]["net_per_year_brl"],
                                default=None) for mk in cfg["markets"]}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{run_id}.json"
    path.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    return path


def _ekey(r):
    return (r["market"], r["tf"], r["entry"]["box_min"], r["entry"]["ratio_max"], r["entry"]["direction"], r["exit"])


def select(rows: list[dict], cfg: dict) -> list[dict]:
    sel, g = cfg["selection"], cfg["entry_grid"]
    by = {_ekey(r): r for r in rows}
    for r in rows:
        m = r["measured"]
        net = m.get("mean_net_brl")
        fails = []
        if m["trades_per_year"] < sel["min_trades_per_year"]:
            fails.append("trades_per_year")
        if net is None or not net > sel["mean_net_brl_measured_gt"]:
            fails.append("mean_net")
        if m["positive_slices"] < sel["min_positive_slices"]:
            fails.append("positive_slices")
        if net is None or not net > r["random_mean_net_brl"]:
            fails.append("beats_random")
        mk, tf, b, q, d, x = _ekey(r)
        nb = []
        for name, vals, val in (("box_min", g["box_min"], b), ("ratio_max", g["ratio_max"], q)):
            i = vals.index(val)
            for j in (i - 1, i + 1):
                if 0 <= j < len(vals):
                    kk = (mk, tf, vals[j] if name == "box_min" else b, vals[j] if name == "ratio_max" else q, d, x)
                    nb.append(by.get(kk))
        nb += [by.get((mk, tf, b, q, d, y)) for y in cfg["exit_neighbours"].get(x, [])]
        nb = [z for z in nb if z is not None]
        pos = [z for z in nb if (z["measured"].get("mean_net_brl") or -1) > 0]
        r["positive_neighbour_share"] = len(pos) / len(nb) if nb else 0.0
        if not nb or r["positive_neighbour_share"] < 2 / 3 - 1e-9:
            fails.append("plateau")
        r["fails"] = fails
        r["candidate"] = not fails
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.p026_lab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--market", action="append")
    a = ap.parse_args(argv)
    print(run(a.market))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
