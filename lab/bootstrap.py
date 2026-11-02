"""Block-bootstrap of a strategy's trade sequence: how bad could the drawdown
have been with the same trades in a different order?

The backtest shows one path. With the whole balance in every trade, the order
of wins and losses decides the drawdown, so this resamples the exported
`profit_ratio` values (base cost scenario) in blocks, compounds each resample
and reports the distribution of max drawdown and final return.

Limits, stated so the output is not over-read:
- Drawdown is measured on closed-trade equity only; intratrade drawdown is not
  visible in the trade list, so the real figure is at least this large.
- Resampling trades assumes they are exchangeable apart from the block
  structure. It does not create new market regimes, so it is a sensitivity
  check on ordering, not a forecast.
- Read it per pair; three correlated pairs are not independent samples.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def load_profit_ratios(csv_path: Path) -> list[float]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = sorted(csv.DictReader(handle), key=lambda row: row["open_date"])
    return [float(row["profit_ratio"]) for row in rows]


def max_drawdown(ratios: list[float]) -> float:
    """Max peak-to-trough fall of the compounded closed-trade equity, as a fraction."""
    equity = peak = 1.0
    worst = 0.0
    for ratio in ratios:
        equity *= 1.0 + ratio
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) / peak)
    return worst


def final_return(ratios: list[float]) -> float:
    equity = 1.0
    for ratio in ratios:
        equity *= 1.0 + ratio
    return equity - 1.0


def _quantile(sorted_values: list[float], q: float) -> float:
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def block_bootstrap(
    ratios: list[float],
    *,
    block_size: int = 3,
    n_resamples: int = 10000,
    seed: int = 1,
    dd_limit: float = 0.25,
) -> dict:
    """Circular block bootstrap with a fixed seed so a result can be reproduced."""
    if not ratios:
        raise ValueError("no trades to resample")
    if block_size < 1:
        raise ValueError("block_size must be at least 1")
    rng = random.Random(seed)
    n = len(ratios)
    drawdowns: list[float] = []
    returns: list[float] = []
    for _ in range(n_resamples):
        sample: list[float] = []
        while len(sample) < n:
            start = rng.randrange(n)
            sample.extend(ratios[(start + i) % n] for i in range(block_size))
        sample = sample[:n]
        drawdowns.append(max_drawdown(sample))
        returns.append(final_return(sample))
    drawdowns.sort()
    returns.sort()
    return {
        "trades": n,
        "block_size": block_size,
        "n_resamples": n_resamples,
        "seed": seed,
        "observed_max_drawdown": max_drawdown(ratios),
        "observed_return": final_return(ratios),
        "drawdown_p50": _quantile(drawdowns, 0.50),
        "drawdown_p95": _quantile(drawdowns, 0.95),
        "drawdown_p99": _quantile(drawdowns, 0.99),
        "prob_drawdown_over_limit": sum(d > dd_limit for d in drawdowns) / n_resamples,
        "return_p05": _quantile(returns, 0.05),
        "return_p50": _quantile(returns, 0.50),
        "prob_negative_return": sum(r <= 0 for r in returns) / n_resamples,
        "dd_limit": dd_limit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trades_csv", nargs="+", type=Path)
    parser.add_argument("--block-size", type=int, default=3)
    parser.add_argument("--resamples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)
    for path in args.trades_csv:
        r = block_bootstrap(
            load_profit_ratios(path), block_size=args.block_size, n_resamples=args.resamples, seed=args.seed
        )
        print(
            f"{path.name}: n={r['trades']} observed DD={r['observed_max_drawdown']:.1%} "
            f"ret={r['observed_return']:+.0%} | DD p50={r['drawdown_p50']:.1%} p95={r['drawdown_p95']:.1%} "
            f"p99={r['drawdown_p99']:.1%} P(DD>{r['dd_limit']:.0%})={r['prob_drawdown_over_limit']:.0%} | "
            f"ret p05={r['return_p05']:+.0%} P(ret<=0)={r['prob_negative_return']:.1%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
