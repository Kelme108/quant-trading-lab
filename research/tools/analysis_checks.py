"""Smoke backtest + lookahead-analysis + recursive-analysis of one registered strategy on the three pairs
(exploration window only). usage: python research/tools/analysis_checks.py <StrategyName> [timeframe]"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import costs, runner  # noqa: E402

name = sys.argv[1]
tf = sys.argv[2] if len(sys.argv) > 2 else "1h"
splits = runner.load_splits()
fee = costs.get_scenario("base").effective_fee_per_side
out = {}
for pair in runner.enabled_pairs():
    tr = runner.resolve_split_timerange("exploration", splits, pair=pair)
    tag = f"{name.lower()}-{pair.replace('/', '-').lower()}"
    ok, text = runner.smoke_backtest(strategy=name, pair=pair, timerange=tr)
    la = runner.run_lookahead_analysis(experiment_id=f"check-la-{tag}", strategy=name, timerange=tr, fee=fee, pair=pair, timeframe=tf)
    rec = runner.run_recursive_analysis(experiment_id=f"check-rec-{tag}", strategy=name, timerange=tr, pair=pair, timeframe=tf)
    out[pair] = {"smoke_ok": ok, "lookahead_has_bias": la.get("lookahead_has_bias"),
                 "lookahead_row": la.get("lookahead_raw_row"), "recursive_is_stable": rec.get("recursive_is_stable"),
                 "recursive_nonzero_cells": rec.get("recursive_nonzero_cells")}
    print(pair, json.dumps({k: v for k, v in out[pair].items() if k != "lookahead_row"}), flush=True)
(ROOT / "research" / "baselines" / f"checks-{name}.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
