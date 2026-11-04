"""Pre-declared sensitivity of H-011/H-012 constants (BTC/USDT 1h, exploration, base cost, full exposure).

Every variant is reported; none is selected. Temporary strategy copies are written to user_data/strategies and
removed afterwards. The variants count as extra tests of their families in the dossier (see docs).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from lab import costs, runner  # noqa: E402

STRATS = ROOT / "user_data" / "strategies"
EMA = ("EMASnapbackATR_H012_v1", [
    ("z1.5", {"Z_ENTRY": "1.5"}), ("z2.5", {"Z_ENTRY": "2.5"}), ("z3.0", {"Z_ENTRY": "3.0"}),
    ("rsi<=35", {"USE_RSI": "True"}), ("vol>=1x", {"USE_VOLUME": "True"}),
    ("exit_rr1.5", {"EXIT_MODE": '"rr"'}), ("stop1.5atr", {"ATR_STOP_MULT": "1.5"}), ("stop3atr", {"ATR_STOP_MULT": "3.0"}),
])
TB = ("TripleBottomReversal_H011_v1", [
    ("tol3%", {"TOLERANCE": "0.03"}), ("tol4%_rebound2%", {"TOLERANCE": "0.04", "MIN_REBOUND": "0.02"}),
    ("k3_sep8", {"PIVOT_K": "3", "MIN_SEPARATION": "8"}),
    ("loose(k3,tol4,reb2,sep8,wait60)", {"PIVOT_K": "3", "TOLERANCE": "0.04", "MIN_REBOUND": "0.02", "MIN_SEPARATION": "8", "MAX_WAIT": "60"}),
    ("vol_off", {"VOLUME_MULT": "0.0"}), ("ema200", {"USE_EMA200": "True"}), ("rsi_div", {"USE_RSI_DIVERGENCE": "True"}),
])


def variant(source: str, base: str, tag: str, changes: dict) -> tuple[str, str]:
    name = re.sub(r"[^A-Za-z0-9]", "", base.split("_")[0]) + "Sens" + re.sub(r"[^A-Za-z0-9]", "", tag) + "_H999_v1"
    text = source.replace(base, name)
    for key, value in changes.items():
        text, n = re.subn(rf"^{key} = .*$", f"{key} = {value}", text, flags=re.M)
        assert n == 1, key
    return name, text


def main() -> None:
    splits = runner.load_splits()
    timerange = runner.resolve_split_timerange("exploration", splits, pair="BTC/USDT")
    fee = costs.get_scenario("base").effective_fee_per_side
    out = []
    for base, variants in (EMA, TB):
        source = (STRATS / f"{base}.py").read_text(encoding="utf-8")
        for tag, changes in [("baseline", {})] + variants:
            name, text = variant(source, base, tag, changes)
            path = STRATS / f"{name}.py"
            path.write_text(text, encoding="utf-8")
            try:
                res = runner.run_backtest(experiment_id=f"sens-{name}", strategy=name, timerange=timerange, fee=fee,
                                          pair="BTC/USDT")
                stats = runner.read_strategy_stats(ROOT / res["artifact_path"]) if res.get("status") == "completed" else {}
            finally:
                path.unlink(missing_ok=True)
            row = {"family": base, "variant": tag, "trades": stats.get("total_trades"), "win_rate": stats.get("winrate"),
                   "profit_factor": stats.get("profit_factor"), "expectancy_ratio": stats.get("expectancy_ratio"),
                   "profit_total": stats.get("profit_total"), "max_dd": stats.get("max_drawdown_account")}
            out.append(row)
            print(json.dumps(row), flush=True)
    (ROOT / "research" / "dossiers").mkdir(exist_ok=True)
    (ROOT / "research" / "dossiers" / "sensitivity-btc-1h.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
