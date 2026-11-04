"""Standard metrics of one strategy on the EXPLORATION split only (audit phase 2).

Reads nothing outside the exploration window: backtests use runner.resolve_split_timerange("exploration"), the hourly
data is cut at each pair's exploration end, and the cycle windows are clipped to it. The validation split and the
prospective holdout are not touched. Numbers come from Freqtrade exports (base and base_2x) and lab/analytics.py,
lab/returns.py, lab/stats.py; the optimistic/conservative/stress rows come from the stored facts.json.

References on the same window and costs: buy-and-hold and Sma200Baseline (exposure 1.0 and, for comparability with an
exposure-scaled strategy, the same exposure).

usage: python research/tools/audit_exploration.py --hid H-009 --strategy WeeklyBreakoutRegime_H009_v1 --exposure 0.25
       [--archived]   (strategy file lives in user_data/strategies/_archive and is copied in for the run)
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import analytics, costs, cycles, returns, runner, stats  # noqa: E402

STRATS = ROOT / "user_data" / "strategies"
OUT = ROOT / "research" / "audit"
SCENARIOS = ("base", "base_2x")
REFERENCE = "Sma200Baseline"


def load_hourly(pair: str, end) -> pd.DataFrame:
    frame = pd.read_feather(ROOT / "user_data" / "data" / "binance" / f"{pair.replace('/', '_')}-1h.feather")
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame.sort_values("date")
    return frame[frame["date"] <= end].reset_index(drop=True)


def sortino(daily: pd.Series) -> float:
    r = daily.to_numpy()
    down = np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))
    return float(stats.annualise(r.mean() / down)) if down > 0 else float("nan")


def eq_metrics(eq: pd.Series) -> dict:
    s = returns.summarise(eq / eq.iloc[0])
    daily = returns.daily_returns(eq)
    years = len(daily) / 365.0
    s["sortino_annualised"] = sortino(daily)
    s["cagr"] = float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) if years > 0 else None
    s["calmar"] = s["cagr"] / s["max_drawdown"] if s["max_drawdown"] > 0 and s["cagr"] is not None else None
    s["exposure_time"] = None
    return s


def run(label, strategy, pair, scenario, timerange, exposure):
    fee = costs.get_scenario(scenario).effective_fee_per_side
    res = runner.run_backtest(experiment_id=f"audit-{label}-{pair.replace('/', '-').lower()}-{scenario}",
                              strategy=strategy, timerange=timerange, fee=fee, pair=pair, exposure=exposure)
    if res.get("status") != "completed":
        raise SystemExit(f"backtest failed: {label} {pair} {scenario}: {res}")
    zp = ROOT / res["artifact_path"]
    return runner.read_trades(zp), runner.read_starting_balance(zp), res["artifact_path"]


def concentration(trades):
    p = sorted((float(t["profit_abs"]) for t in trades), reverse=True)
    total = sum(p)
    return {f"top{k}": (sum(p[:k]) / total if total > 0 else None) for k in (1, 5, 10)}


def position_mask(trades, index):
    mask = pd.Series(False, index=index)
    for t in trades:
        mask[(index >= pd.Timestamp(t["open_date"])) & (index <= pd.Timestamp(t["close_date"]))] = True
    return mask


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hid", required=True)
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--exposure", type=float, default=1.0)
    ap.add_argument("--archived", action="store_true")
    a = ap.parse_args()
    splits = runner.load_splits()
    pairs = runner.enabled_pairs()
    copied = None
    if a.archived:
        src = STRATS / "_archive" / f"{a.strategy}.py"
        copied = STRATS / f"{a.strategy}.py"
        shutil.copy2(src, copied)
    result = {"hypothesis": a.hid, "strategy": a.strategy, "exposure": a.exposure, "window": "exploration only",
              "validation_read": False, "holdout_read": False, "pairs": {}}
    try:
        for pair in pairs:
            end = pd.Timestamp(splits["pairs"][pair]["exploration"]["end_utc"])
            start = pd.Timestamp(splits["pairs"][pair]["exploration"]["start_utc"])
            cycles.assert_before_holdout(end)
            hourly = load_hourly(pair, end)
            tr = runner.resolve_split_timerange("exploration", splits, pair=pair)
            days = (end - start).days
            out = {"days": days, "scenarios": {}}
            eqs, dailys = {}, {}
            for sc in SCENARIOS:
                fee = costs.get_scenario(sc).effective_fee_per_side
                trades, bal, art = run(a.hid.lower(), a.strategy, pair, sc, tr, a.exposure)
                ref_trades, ref_bal, ref_art = run("sma200", REFERENCE, pair, sc, tr, 1.0)
                eq = returns.equity_curve(trades, hourly, exposure=a.exposure, fee_per_side=fee)
                ref_eq = returns.equity_curve(ref_trades, hourly, exposure=1.0, fee_per_side=fee)
                ref_eq_same = returns.equity_curve(ref_trades, hourly, exposure=a.exposure, fee_per_side=fee)
                bh = returns.buy_and_hold_equity(hourly, start=hourly["date"].iloc[0], end=end, fee_per_side=fee)
                m = analytics.trade_metrics(trades, bal)
                for key in ("histogram", "monthly"):
                    m.pop(key, None)
                m["concentration"] = concentration(trades)
                m["equity"] = eq_metrics(eq)
                in_pos = position_mask(trades, eq.index)
                m["equity"]["exposure_time"] = float(in_pos.mean())
                m["buy_and_hold"] = eq_metrics(bh)
                m["sma200_exposure_1"] = eq_metrics(ref_eq)
                m["sma200_same_exposure"] = eq_metrics(ref_eq_same)
                m["sma200_trades"] = len(ref_trades)
                d, rd, bd = returns.daily_returns(eq), returns.daily_returns(ref_eq_same), returns.daily_returns(bh)
                m["corr_daily_vs_sma200"] = float(d.corr(rd))
                m["corr_daily_vs_buy_and_hold"] = float(d.corr(bd))
                ref_pos = position_mask(ref_trades, eq.index)
                m["overlap_in_position_with_sma200"] = float((in_pos & ref_pos).sum() / max(in_pos.sum(), 1))
                m["ci_mean_trade_return"] = stats.block_bootstrap_ci(
                    [float(t["profit_ratio"]) for t in trades], lambda x: float(x.mean()), block=3)
                m["ci_total_return"] = stats.block_bootstrap_ci(
                    [float(t["profit_ratio"]) for t in trades],
                    lambda x: float(np.prod(1 + a.exposure * x) - 1), block=3)
                windows = {}
                for name, (s0, s1) in cycles.cycles().items():
                    s1 = min(s1, end)
                    if s0 >= end:
                        continue
                    part = eq[(eq.index >= s0) & (eq.index <= s1)]
                    hp = bh[(bh.index >= s0) & (bh.index <= s1)]
                    rp = ref_eq_same[(ref_eq_same.index >= s0) & (ref_eq_same.index <= s1)]
                    if len(part) < 48:
                        continue
                    windows[name] = {
                        "trades": sum(1 for t in trades if s0 <= pd.Timestamp(t["open_date"]) <= s1),
                        "strategy_return": float(part.iloc[-1] / part.iloc[0] - 1),
                        "strategy_maxdd": float((1 - part / part.cummax()).max()),
                        "buy_and_hold_return": float(hp.iloc[-1] / hp.iloc[0] - 1),
                        "sma200_same_exposure_return": float(rp.iloc[-1] / rp.iloc[0] - 1)}
                m["cycles"] = windows
                m["artifact"] = art
                out["scenarios"][sc] = m
                eqs[sc], dailys[sc] = eq, d
            result["pairs"][pair] = out
            print(pair, {s: out["scenarios"][s]["trades"] for s in SCENARIOS}, flush=True)
        base = {p: result["pairs"][p]["scenarios"]["base"]["net_profit_abs"] / result["pairs"][p]["days"] for p in pairs}
        result["consistency_min_over_max_base"] = (min(base.values()) / max(base.values())
                                                   if min(base.values()) > 0 else 0.0)
    finally:
        if copied:
            copied.unlink(missing_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{a.hid}-exploration-metrics.json"
    path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
