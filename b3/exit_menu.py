"""Exit menu over the conveyor's screened families (b3/config/exit_menu.json): the same entries, four
volatility-scaled exits (stop/target/breakeven/trailing in units of V), exploration only.

    python -m b3.exit_menu run [--family E-001 ...] [--market WIN]

While it runs it writes only under ops/state/exit_menu/ (ignored by git), so the conveyor's file guard never sees it;
the report is moved to research/b3/exit_menu/ and committed afterwards.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from b3 import esteira as es
from b3 import p026_lab as lab
from b3 import pattern_search as ps

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "b3" / "config" / "exit_menu.json"
WORK = ROOT / "ops" / "state" / "exit_menu"


def load_config() -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not cfg.get("approved_by_owner") or cfg.get("split") != "exploration":
        raise SystemExit("exit menu: config not approved or not on exploration")
    return cfg


def screened_families() -> list[es.Family]:
    rows = {}
    for line in (es.OUT / "families.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["family"]] = r
    out = []
    for f in es.load_families():
        r = rows.get(f.id)
        if r and not r.get("rejected") and r.get("code_hash") == f.code_hash:
            out.append(f)
    return out


def select(rows: list[dict], fam: es.Family, cfg: dict) -> None:
    sel = cfg["selection"]
    by = {(r["tf"], json.dumps(r["params"], sort_keys=True, default=str), r["exit"]): r for r in rows}
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
        nb = [by.get((r["tf"], json.dumps(q, sort_keys=True, default=str), r["exit"]))
              for q in es.neighbours(fam.grid, r["params"])]
        nb += [by.get((r["tf"], json.dumps(r["params"], sort_keys=True, default=str), y))
               for y in cfg["exit_neighbours"].get(r["exit"], [])]
        nb = [z for z in nb if z is not None]
        pos = [z for z in nb if (z["measured"].get("mean_net_brl") or -1) > 0]
        r["positive_neighbour_share"] = len(pos) / len(nb) if nb else 0.0
        if not nb or r["positive_neighbour_share"] < 2 / 3 - 1e-9:
            fails.append("plateau")
        r["fails"] = fails


def run(only: list[str] | None = None, markets: list[str] | None = None) -> Path:
    from b3.markets import market
    cfg = load_config()
    ecfg = es.load_config()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    WORK.mkdir(parents=True, exist_ok=True)
    ledger = WORK / "ledger.jsonl"
    report = {"run": run_id, "config": "b3/config/exit_menu.json", "split": "exploration", "families": {}, "picks": []}
    fams = [f for f in screened_families() if only is None or f.id in only]
    ps_cfg = ps.load_config()
    t0 = time.time()
    maxd = cfg["max_entries_per_session"]
    for mk in markets or ecfg["markets"]:
        fm = [f for f in fams if mk in f.markets]
        if not fm:
            continue
        ps.set_market(mk)
        start, end = ps.split_bounds("exploration")
        inst = market(mk).instrument()
        cost = es.costs_for(mk)
        tick, pv = inst.tick_size, inst.point_value_brl
        frames, ctxs, mins = {}, {}, None
        for f in fm:
            rows = []
            for tf in f.timeframes:
                if tf not in frames:
                    frames[tf] = ps.load_frame(tf, end, ps_cfg)
                    ctxs[tf] = es.Ctx(frames[tf])
                fr, ctx = frames[tf], ctxs[tf]
                ctx._cache = {k: v for k, v in ctx._cache.items() if k == "exit_menu_V"}   # memory flat across families
                if mins is None:
                    mins = es.load_minutes(mk, fr.rules, fr.cal, end)
                m30 = ctx.bars(30)
                V = ctx.cached("exit_menu_V", lambda: ctx.same_minute(np.abs(ctx.c / ctx.prev(ctx.c, m30) - 1.0), "mean"))
                for p in f.variants():
                    try:
                        d = es.directions(f, fr, p, ctx=ctx)
                    except Exception as e:                       # noqa: BLE001 - one broken family must not stop the night
                        rows.append({"tf": tf, "params": p, "error": repr(e)[:300]})
                        continue
                    k = np.flatnonzero((d != 0) & fr.entry_ok & (fr.now >= start.value))
                    e_ns, side = fr.now[k], d[k].astype(int)
                    i0 = np.array([mins.pos.get(int(x), -1) for x in e_ns], dtype=np.int64)
                    Vp = V[k]
                    ok = (i0 >= 0) & np.isfinite(Vp) & (Vp > 0)
                    e_ns, side, i0, Vp = e_ns[ok], side[ok], i0[ok], Vp[ok]
                    E = mins.open[i0] if len(i0) else np.array([])
                    nan = np.full(len(E), np.nan)
                    for ex_id, spec in cfg["exits"].items():
                        dist = lab.distances(spec, E, nan, nan, Vp, pv, tick)
                        tm = lab.simulate(i0, side, e_ns, mins, dist, spec["hold_min"], inst, cost["measured"], maxd)
                        row = {"variant": es.vkey(f.id, mk, tf, p), "tf": tf, "params": p, "exit": ex_id,
                               "measured": lab.summary(tm, start, end, cfg["selection"]["time_slices"])}
                        row["_args"] = (i0, side, e_ns, dist, spec["hold_min"])
                        rows.append(row)
                        with ledger.open("a", encoding="utf-8") as fh:
                            fh.write(json.dumps({"variant": row["variant"], "exit": ex_id, "run": run_id,
                                                 "split": "exploration", "trades": int(len(tm))}) + "\n")
            good = [r for r in rows if "error" not in r]
            select(good, f, cfg)
            for r in good:
                if r["fails"]:
                    continue
                i0, side, e_ns, dist, hold = r["_args"]
                tp = lab.simulate(i0, side, e_ns, mins, dist, hold, inst, cost["measured_p90"], maxd)
                r["measured_p90_mean_net_brl"] = float(tp["net_brl"].mean()) if len(tp) else None
                rng = np.random.default_rng(32)
                rnd = []
                for _ in range(cfg["random_control"]["seeds"]):
                    ri, rs, keep = lab.randomise(i0, mins, start.value, rng)
                    dr = {kk: vv[keep] for kk, vv in dist.items()}
                    tr = lab.simulate(ri, rs, mins.time[ri], mins, dr, hold, inst, cost["measured"], maxd)
                    rnd.append(float(tr["net_brl"].mean()) if len(tr) else 0.0)
                r["random_mean_net_brl"] = float(np.mean(rnd))
                if not r["measured"]["mean_net_brl"] > r["random_mean_net_brl"]:
                    r["fails"].append("beats_random")
            for r in rows:
                r.pop("_args", None)
                r["candidate"] = "error" not in r and not r["fails"]
            cands = [r for r in rows if r.get("candidate")]
            pick = max(cands, key=lambda r: r["measured"].get("net_per_year_brl", 0.0), default=None)
            best = max(good, key=lambda r: r["measured"].get("mean_net_brl") or -1e9, default=None)
            report["families"].setdefault(f.id, {"title": f.title})[mk] = {
                "versions": len(rows), "candidates": len(cands), "pick": pick,
                "best_mean_net": None if best is None else {"variant": best["variant"], "exit": best["exit"],
                                                             "mean_net_brl": best["measured"].get("mean_net_brl"),
                                                             "trades_per_year": best["measured"]["trades_per_year"]},
                "errors": [r for r in rows if "error" in r][:3]}
            if pick:
                report["picks"].append({"family": f.id, "market": mk, "variant": pick["variant"], "exit": pick["exit"],
                                        "mean_net_brl": pick["measured"]["mean_net_brl"],
                                        "p90": pick.get("measured_p90_mean_net_brl"),
                                        "trades_per_year": pick["measured"]["trades_per_year"],
                                        "net_per_year_brl": pick["measured"].get("net_per_year_brl"),
                                        "random": pick.get("random_mean_net_brl")})
            print(f"{f.id} {mk}: {len(rows)} versions, {len(cands)} candidates"
                  f"{' pick ' + pick['variant'] + ' ' + pick['exit'] if pick else ''} ({time.time() - t0:.0f}s)", flush=True)
            report["n_versions_read"] = sum(v[m]["versions"] for v in report["families"].values() for m in v if m != "title")
            (WORK / f"{run_id}.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    ps.set_market("WIN")
    with (WORK / "picks.jsonl").open("a", encoding="utf-8") as fh:      # every pick of every run, for the demo step
        for p in report["picks"]:
            fh.write(json.dumps(dict(p, run=run_id)) + "
")
    return WORK / f"{run_id}.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="b3.exit_menu")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--family", action="append")
    r.add_argument("--market", action="append")
    a = ap.parse_args(argv)
    print(run(a.family, a.market))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
