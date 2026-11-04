"""Step 2.5-2.6: exploration of a pre-registered grid. IS (exploration split) only; validation and holdout are not read.

usage: python research/tools/grid_explore.py <H-id>      (family specs in FAMILIES below)

Procedure (fixed before the first run of H-015, reused unchanged for later families):
 1. Every configuration is a temporary copy of the registered file with module constants replaced (never edits the
    registered file), backtested per pair on the pair's exploration split at the base fee. Trades are exported.
 2. Equity per cost scenario (base, base_2x) is rebuilt from the exported trades with that scenario's fee
    (lab/returns.py; the rates do not depend on the fee, checked once against a real base_2x run for the winner).
 3. Per-config return series = equal-weight average of the pairs' daily returns on the days all three pairs exist.
    The matrix (days x configs) feeds PBO (CSCV, 16 slices), DSR (N = grid size, variance across configs) and the
    anchored walk-forward (folds = calendar years 2020..2024, train = everything before).
 4. Best configuration = highest annualised pooled Sharpe at base_2x. Plateau = every adjacent grid neighbour
    (same other flags, previous/next value of the primary parameter) reaches >= 70% of the best Sharpe.
 5. References at base_2x on the same window: buy-and-hold and Sma200Baseline (equal-weight over the pairs).
 6. Criteria to read validation (all required): DSR >= 0.95, PBO <= 0.5, plateau, Sharpe > B&H and > Sma200Baseline,
    >= 30 trades on every pair for the best configuration, gates of lab/config/gates.json (checked afterwards through
    the official experiment, only if everything above passes). The decision uses the base_2x scenario.
 7. Block-bootstrap CI of the mean trade return of the best configuration (flag low_sample if < 100 trades).
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from lab import costs, cycles, returns, runner, stats, walkforward  # noqa: E402
from baseline_cycles import load_hourly  # noqa: E402

STRATS = ROOT / "user_data" / "strategies"
OUT = ROOT / "research" / "grids"
SCENARIOS = ("base", "base_2x")
REFERENCE = "Sma200Baseline"


def tsmom_grid():
    # (tag, constants to replace, (primary name, primary value, other flag name, other flag value))
    return [(f"N{n}_{'reg' if reg else 'noreg'}", {"N_DAYS": str(n), "USE_REGIME": str(reg)}, ("N_DAYS", n, "USE_REGIME", reg))
            for reg in (False, True) for n in (30, 60, 90, 120, 180)]


FAMILIES = {
    "H-015": {"file": "TimeSeriesMomentum_H015_v1", "timeframe": "1h", "grid": tsmom_grid(), "values": [30, 60, 90, 120, 180]},
}


def make_copy(source: str, base: str, tag: str, changes: dict) -> tuple[str, str]:
    name = "Grid" + re.sub(r"[^A-Za-z0-9]", "", base.split("_")[0]) + re.sub(r"[^A-Za-z0-9]", "", tag) + "_H999_v1"
    text = source.replace(base, name)
    for key, value in changes.items():
        text, n = re.subn(rf"^{key} = .*$", f"{key} = {value}", text, flags=re.M)
        assert n == 1, key
    return name, text


def pooled(daily_by_pair: dict) -> pd.Series:
    return pd.DataFrame(daily_by_pair).dropna().mean(axis=1)


def sharpe_ann(series) -> float:
    return stats.annualise(stats.sharpe(np.asarray(series, dtype=float)))


def main(hid: str) -> int:
    spec = FAMILIES[hid]
    splits = runner.load_splits()
    pairs = runner.enabled_pairs()
    source_path = STRATS / f"{spec['file']}.py"
    if not source_path.exists():
        source_path = STRATS / "_archive" / f"{spec['file']}.py"
    source = source_path.read_text(encoding="utf-8")
    fee_of = {s: costs.get_scenario(s).effective_fee_per_side for s in SCENARIOS}
    hourly, is_end, trades_of = {}, {}, {}
    for pair in pairs:
        end = pd.Timestamp(splits["pairs"][pair]["exploration"]["end_utc"])
        h = load_hourly(pair)
        hourly[pair], is_end[pair] = h[h["date"] <= end].reset_index(drop=True), end
    runs = list(spec["grid"])
    for tag, changes, _ in runs + [(REFERENCE, None, None)]:
        for pair in pairs:
            timerange = runner.resolve_split_timerange("exploration", splits, pair=pair)
            path = None
            if changes is None:
                name = REFERENCE
            else:
                name, text = make_copy(source, spec["file"], tag, changes)
                path = STRATS / f"{name}.py"
                path.write_text(text, encoding="utf-8")
            try:
                run = runner.run_backtest(
                    experiment_id=f"grid-{hid.lower()}-{tag.lower()}-{pair.replace('/', '-').lower()}",
                    strategy=name, timerange=timerange, fee=fee_of["base"], pair=pair,
                    timeframe="1h" if changes is None else spec["timeframe"])
            finally:
                if path:
                    path.unlink(missing_ok=True)
            if run.get("status") != "completed":
                print("FAILED", tag, pair, run)
                return 2
            trades_of[(tag, pair)] = runner.read_trades(ROOT / run["artifact_path"])
            print(tag, pair, "trades", len(trades_of[(tag, pair)]), flush=True)
    tags = [t for t, _, _ in runs]
    daily, equity = {}, {}
    for tag in tags + [REFERENCE]:
        for scenario in SCENARIOS:
            for pair in pairs:
                eq = returns.equity_curve(trades_of[(tag, pair)], hourly[pair], fee_per_side=fee_of[scenario])
                equity[(tag, scenario, pair)] = eq
                daily[(tag, scenario, pair)] = returns.daily_returns(eq)
    hold_daily = {}
    for scenario in SCENARIOS:
        for pair in pairs:
            eq = returns.buy_and_hold_equity(hourly[pair], start=hourly[pair]["date"].iloc[0], end=is_end[pair],
                                             fee_per_side=fee_of[scenario])
            hold_daily[(scenario, pair)] = returns.daily_returns(eq)
    result = {"hypothesis": hid, "n_trials": len(tags), "validation_read": False, "holdout_read": False, "configs": {}, "pairs": pairs}
    series = {s: pd.DataFrame({t: pooled({p: daily[(t, s, p)] for p in pairs}) for t in tags}) for s in SCENARIOS}
    ref = {s: pooled({p: daily[(REFERENCE, s, p)] for p in pairs}) for s in SCENARIOS}
    bh = {s: pooled({p: hold_daily[(s, p)] for p in pairs}) for s in SCENARIOS}
    by_key = {t: key for t, _, key in runs}
    values = spec["values"]
    for scenario in SCENARIOS:
        matrix = series[scenario]
        sharpes = {t: sharpe_ann(matrix[t]) for t in tags}
        for t in tags:
            per_pair = {}
            for p in pairs:
                eq = equity[(t, scenario, p)]
                per_pair[p] = {**returns.summarise(eq / eq.iloc[0]), "trades": len(trades_of[(t, p)])}
            result["configs"].setdefault(t, {})[scenario] = {"pooled_sharpe": sharpes[t], "per_pair": per_pair}
        best = max(tags, key=sharpes.get)
        trial_var = stats.trial_sharpe_variance([matrix[t].to_numpy() for t in tags])
        dsr = stats.deflated_sharpe(matrix[best].to_numpy(), len(tags), trial_var)
        pbo = stats.pbo_cscv(matrix.to_numpy(), 16)
        wf = walkforward.walk_forward(matrix, walkforward.anchored_folds(matrix.index, 2020, 2024))
        wf.pop("oos_returns", None)
        key = by_key[best]
        i = values.index(key[1])
        near = [values[j] for j in (i - 1, i + 1) if 0 <= j < len(values)]
        neighbours = [t for t in tags if by_key[t][2:] == key[2:] and by_key[t][1] in near]
        plateau = {"neighbours": neighbours,
                   "ratios": {n: (sharpes[n] / sharpes[best] if sharpes[best] > 0 else None) for n in neighbours},
                   "pass": bool(sharpes[best] > 0 and neighbours and all(sharpes[n] >= 0.7 * sharpes[best] for n in neighbours))}
        trade_returns = [float(x["profit_ratio"]) for p in pairs for x in sorted(trades_of[(best, p)], key=lambda x: x["open_date"])]
        ci = stats.block_bootstrap_ci(trade_returns, lambda x: float(x.mean()), block=3)
        per_pair_best = result["configs"][best][scenario]["per_pair"]
        crit = {
            "dsr": dsr["dsr"], "dsr_pass": bool(dsr["dsr"] >= 0.95),
            "pbo": pbo["pbo"], "pbo_pass": bool(pbo["pbo"] <= 0.5),
            "plateau_pass": plateau["pass"],
            "sharpe_best": sharpes[best], "sharpe_buy_and_hold": sharpe_ann(bh[scenario].reindex(matrix.index)),
            "sharpe_sma200": sharpe_ann(ref[scenario].reindex(matrix.index)),
            "min_trades_per_pair": min(v["trades"] for v in per_pair_best.values()),
        }
        crit["beats_buy_and_hold"] = bool(crit["sharpe_best"] > crit["sharpe_buy_and_hold"])
        crit["beats_sma200"] = bool(crit["sharpe_best"] > crit["sharpe_sma200"])
        crit["trades_pass"] = bool(crit["min_trades_per_pair"] >= 30)
        crit["all_pass_before_gates"] = bool(crit["dsr_pass"] and crit["pbo_pass"] and crit["plateau_pass"]
                                             and crit["beats_buy_and_hold"] and crit["beats_sma200"] and crit["trades_pass"])
        windows = {}
        for name, (a, b) in cycles.cycles().items():
            a, b = max(a, matrix.index[0]), min(b, matrix.index[-1])
            if (b - a).days < 60:
                continue
            windows[f"cycle {name}"] = {
                "best": sharpe_ann(matrix[best].loc[a:b]), "buy_and_hold": sharpe_ann(bh[scenario].loc[a:b]),
                "sma200": sharpe_ann(ref[scenario].loc[a:b]),
                "best_return": float((1 + matrix[best].loc[a:b]).prod() - 1), "bh_return": float((1 + bh[scenario].loc[a:b]).prod() - 1)}
        result.setdefault("selection", {})[scenario] = {
            "best": best, "dsr": dsr, "trial_sharpe_variance": trial_var, "pbo": pbo, "walk_forward": wf, "plateau": plateau,
            "criteria": crit, "mean_trade_return_ci": ci, "windows": windows, "all_sharpes": sharpes,
            "days": int(len(matrix)), "window": [str(matrix.index[0].date()), str(matrix.index[-1].date())]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{hid}-exploration.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    for scenario in SCENARIOS:
        sel = result["selection"][scenario]
        print(scenario, "best", sel["best"], json.dumps(sel["criteria"], default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
