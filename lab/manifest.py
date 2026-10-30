"""Fill research/experiment-manifest.yaml's template and write it to
research/manifests/<experiment-id>.yaml.

No PyYAML (stdlib only, per the task's constraints): this writes YAML by
hand, matching the template's structure and quoting style closely enough
for a human or a simple parser to read. It refuses to overwrite an existing
manifest file, mirroring the "never overwrite prior artifacts" rule.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFESTS_DIR = Path(__file__).parents[1] / "research" / "manifests"


def _yaml_scalar(value) -> str:
    """Render a single scalar the way the template does: quoted strings,
    bare numbers/booleans, `null` for None."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # String: quote it. Escape embedded double quotes and backslashes.
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _yaml_mapping_inline(mapping: dict) -> str:
    """Render a small flat dict as inline YAML, e.g. {"0": 100.0} -> {"0": 100.0}."""
    if not mapping:
        return "{}"
    parts = [f'{_yaml_scalar(str(k))}: {_yaml_scalar(v)}' for k, v in mapping.items()]
    return "{" + ", ".join(parts) + "}"


def render_manifest(data: dict) -> str:
    """Render the manifest dict into the same structure/order as
    research/experiment-manifest.yaml."""
    code = data["code"]
    runtime = data["runtime"]
    market = data["market"]
    dataset = data["data"]
    backtest = data["backtest"]
    validation = data["validation"]
    result = data["result"]

    lines = []
    lines.append(f'experiment_id: {_yaml_scalar(data["experiment_id"])}')
    lines.append(f'created_at_utc: {_yaml_scalar(data["created_at_utc"])}')
    lines.append("")
    lines.append("code:")
    lines.append(f'  repository_state: {_yaml_scalar(code["repository_state"])}')
    lines.append(f'  git_commit: {_yaml_scalar(code["git_commit"])}')
    lines.append(f'  strategy_file: {_yaml_scalar(code["strategy_file"])}')
    lines.append(f'  strategy_sha256: {_yaml_scalar(code["strategy_sha256"])}')
    lines.append(f'  config_sha256_redacted: {_yaml_scalar(code["config_sha256_redacted"])}')
    lines.append("")
    lines.append("runtime:")
    lines.append(f'  freqtrade_version: {_yaml_scalar(runtime["freqtrade_version"])}')
    lines.append(f'  ccxt_version: {_yaml_scalar(runtime["ccxt_version"])}')
    lines.append(f'  docker_image: {_yaml_scalar(runtime["docker_image"])}')
    lines.append(f'  docker_image_digest: {_yaml_scalar(runtime["docker_image_digest"])}')
    lines.append(f'  host: {_yaml_scalar(runtime["host"])}')
    lines.append(f'  command: {_yaml_scalar(runtime["command"])}')
    lines.append("")
    lines.append("market:")
    lines.append(f'  exchange: {_yaml_scalar(market["exchange"])}')
    lines.append(f'  market_type: {_yaml_scalar(market["market_type"])}')
    lines.append(f'  pair: {_yaml_scalar(market["pair"])}')
    lines.append(f'  timeframe: {_yaml_scalar(market["timeframe"])}')
    lines.append(f'  candle_type: {_yaml_scalar(market["candle_type"])}')
    lines.append(f'  timezone: {_yaml_scalar(market["timezone"])}')
    lines.append("")
    lines.append("data:")
    lines.append(f'  path: {_yaml_scalar(dataset["path"])}')
    lines.append(f'  sha256: {_yaml_scalar(dataset["sha256"])}')
    lines.append(f'  source: {_yaml_scalar(dataset["source"])}')
    lines.append(f'  first_candle_utc: {_yaml_scalar(dataset["first_candle_utc"])}')
    lines.append(f'  last_complete_candle_utc: {_yaml_scalar(dataset["last_complete_candle_utc"])}')
    lines.append(f'  candle_count: {_yaml_scalar(dataset["candle_count"])}')
    lines.append(f'  gaps: {_yaml_scalar(dataset["gaps"])}')
    lines.append(f'  duplicates: {_yaml_scalar(dataset["duplicates"])}')
    lines.append(f'  incomplete_candle_removed: {_yaml_scalar(dataset["incomplete_candle_removed"])}')
    lines.append("")
    lines.append("backtest:")
    lines.append(f'  requested_timerange: {_yaml_scalar(backtest["requested_timerange"])}')
    lines.append(f'  effective_timerange: {_yaml_scalar(backtest["effective_timerange"])}')
    lines.append(f'  startup_candles: {_yaml_scalar(backtest["startup_candles"])}')
    lines.append(f'  strategy: {_yaml_scalar(backtest["strategy"])}')
    lines.append(f'  parameters: {_yaml_mapping_inline(backtest["parameters"])}')
    lines.append(f'  fee_rate_per_side: {_yaml_scalar(backtest["fee_rate_per_side"])}')
    lines.append(f'  slippage_rate_per_side: {_yaml_scalar(backtest["slippage_rate_per_side"])}')
    lines.append(f'  spread_rate: {_yaml_scalar(backtest["spread_rate"])}')
    lines.append(f'  initial_wallet: {_yaml_scalar(backtest["initial_wallet"])}')
    lines.append(f'  stake_amount: {_yaml_scalar(backtest["stake_amount"])}')
    lines.append(f'  max_open_trades: {_yaml_scalar(backtest["max_open_trades"])}')
    lines.append("  order_types:")
    lines.append(f'    entry: {_yaml_scalar(backtest["order_types"]["entry"])}')
    lines.append(f'    exit: {_yaml_scalar(backtest["order_types"]["exit"])}')
    lines.append(f'    stoploss: {_yaml_scalar(backtest["order_types"]["stoploss"])}')
    lines.append("")
    lines.append("validation:")
    lines.append(f'  lookahead_analysis: {_yaml_scalar(validation["lookahead_analysis"])}')
    lines.append(f'  recursive_analysis: {_yaml_scalar(validation["recursive_analysis"])}')
    lines.append(f'  benchmarks: {_yaml_scalar(validation["benchmarks"])}')
    lines.append(f'  walk_forward: {_yaml_scalar(validation["walk_forward"])}')
    lines.append(f'  final_test_unlocked: {_yaml_scalar(validation["final_test_unlocked"])}')
    lines.append(f'  hypotheses_tested_before: {_yaml_scalar(validation["hypotheses_tested_before"])}')
    lines.append("")
    lines.append("result:")
    lines.append(f'  artifact: {_yaml_scalar(result["artifact"])}')
    lines.append(f'  trades: {_yaml_scalar(result["trades"])}')
    lines.append(f'  net_profit_quote: {_yaml_scalar(result["net_profit_quote"])}')
    lines.append(f'  decision: {_yaml_scalar(result["decision"])}')
    lines.append(f'  notes: {_yaml_scalar(result["notes"])}')
    lines.append("")
    return "\n".join(lines)


def write_manifest(experiment_id: str, data: dict, manifests_dir: Path = MANIFESTS_DIR) -> Path:
    """Write research/manifests/<experiment_id>.yaml. Refuses to overwrite."""
    manifests_dir.mkdir(parents=True, exist_ok=True)
    out_path = manifests_dir / f"{experiment_id}.yaml"
    if out_path.exists():
        raise FileExistsError(
            f"manifest already exists at {out_path}; experiments never overwrite "
            "prior manifests. Use a new experiment_id."
        )
    rendered = render_manifest(data)
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


def default_manifest_skeleton() -> dict:
    """A manifest dict matching every field in research/experiment-manifest.yaml,
    with template defaults. Callers fill in the real values before writing."""
    return {
        "experiment_id": "",
        "created_at_utc": "",
        "code": {
            "repository_state": "",
            "git_commit": None,
            "strategy_file": "",
            "strategy_sha256": "",
            "config_sha256_redacted": "",
        },
        "runtime": {
            "freqtrade_version": "",
            "ccxt_version": "",
            "docker_image": "freqtradeorg/freqtrade:2026.9",
            "docker_image_digest": "",
            "host": "",
            "command": "",
        },
        "market": {
            "exchange": "binance",
            "market_type": "spot",
            "pair": "BTC/USDT",
            "timeframe": "1h",
            "candle_type": "spot",
            "timezone": "UTC",
        },
        "data": {
            "path": "",
            "sha256": "",
            "source": "",
            "first_candle_utc": "",
            "last_complete_candle_utc": "",
            "candle_count": 0,
            "gaps": 0,
            "duplicates": 0,
            "incomplete_candle_removed": False,
        },
        "backtest": {
            "requested_timerange": "",
            "effective_timerange": "",
            "startup_candles": 0,
            "strategy": "",
            "parameters": {},
            "fee_rate_per_side": 0.001,
            "slippage_rate_per_side": 0.0,
            "spread_rate": 0.0,
            "initial_wallet": 100.0,
            "stake_amount": "unlimited",
            "max_open_trades": 1,
            "order_types": {"entry": "", "exit": "", "stoploss": ""},
        },
        "validation": {
            "lookahead_analysis": "pending",
            "recursive_analysis": "pending",
            "benchmarks": "pending",
            "walk_forward": "pending",
            "final_test_unlocked": False,
            "hypotheses_tested_before": 0,
        },
        "result": {
            "artifact": "",
            "trades": None,
            "net_profit_quote": None,
            "decision": "pending",
            "notes": "",
        },
    }
