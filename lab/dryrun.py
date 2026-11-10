"""Judge each frozen dry-run bot by its number of closed trades and by all its metrics together.

Owner decision 2026-11-10: the dry-run should not wait for a calendar date; it is decided when the bot has enough closed
trades. The rules are in lab/config/dryrun.json. A verdict is one of:
  collecting         not enough closed trades (or days) yet, and no early reason to stop;
  approved_for_review every metric clears its bar: worth a human look for real money (never an order, never automatic);
  rejected           the evidence says the edge is not there (profit factor under the bar at the minimum trade count,
                     or far under at the early-reject count): stopping the bot is recommended.

Metrics (closed trades only, after the fees the dry-run charged): trades, days, win rate, average win and loss and their
ratio (payoff), profit factor, expectancy per trade (percent of the stake), net profit, profit without the best trade,
maximum drawdown of the closed-trade equity (percent of the wallet), the seeded bootstrap probability that the mean trade
is positive, and the observed entry cost per side against the conservative backtest scenario. The win rate is shown but
never decides alone: a high win rate with a payoff under 1 loses money (the lab's own data show it).
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path

from lab import costs, forward

ROOT = Path(__file__).parents[1]
CONFIG = Path(__file__).parent / "config" / "dryrun.json"
REPORT = "research/forward/verdicts.md"


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bootstrap_prob_positive(returns: list[float], resamples: int, seed: int) -> float:
    """Share of seeded resamples (with replacement) whose mean trade return is above zero."""
    if not returns:
        return 0.0
    rng = random.Random(seed)
    n = len(returns)
    positive = 0
    for _ in range(resamples):
        total = 0.0
        for _ in range(n):
            total += returns[rng.randrange(n)]
        positive += total > 0
    return positive / resamples


def max_drawdown_pct(profits_abs: list[float], wallet: float) -> float:
    """Largest peak-to-trough fall of the closed-trade equity, as a percent of the starting wallet."""
    equity = peak = worst = 0.0
    for profit in profits_abs:
        equity += profit
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return 100.0 * worst / wallet if wallet > 0 else 0.0


def metrics(trades: list[dict], wallet: float, cfg: dict) -> dict:
    """Metrics of closed trades in `closed_as_backtest_trades` shape, ordered by close date."""
    closed = sorted(trades, key=lambda t: t["close_date"])
    returns = [t["profit_ratio"] for t in closed]
    profits = [t["profit_abs"] for t in closed]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p < 0]
    opened = [forward._ts(t["open_date"]) for t in closed]
    closes = [forward._ts(t["close_date"]) for t in closed]
    first, last = (min((d for d in opened if d), default=None), max((d for d in closes if d), default=None))
    gross_loss = -sum(losses)
    boot = cfg["bootstrap"]
    return {
        "trades": len(closed),
        "days": (last - first).total_seconds() / 86400.0 if first and last else 0.0,
        "win_rate": len(wins) / len(closed) if closed else None,
        "avg_win": sum(wins) / len(wins) if wins else None,
        "avg_loss": -sum(losses) / len(losses) if losses else None,
        "payoff": (sum(wins) / len(wins)) / (-sum(losses) / len(losses)) if wins and losses else None,
        "profit_factor": (sum(wins) / gross_loss) if gross_loss > 0 else (float("inf") if wins else None),
        "expectancy_pct": 100.0 * sum(returns) / len(returns) if returns else None,
        "net_profit": sum(profits),
        "net_profit_excl_best": sum(profits) - max(profits) if profits else None,
        "max_drawdown_pct": max_drawdown_pct(profits, wallet),
        "prob_mean_positive": bootstrap_prob_positive(returns, boot["resamples"], boot["seed"]),
    }


def verdict(m: dict, cfg: dict, execution: dict | None = None) -> tuple[str, list[str]]:
    """('collecting' | 'approved_for_review' | 'rejected', reasons). Every checked bar is listed."""
    reasons: list[str] = []
    pf = m["profit_factor"]
    early = cfg["early_reject"]
    if m["trades"] >= early["min_closed_trades"] and pf is not None and pf < early["max_profit_factor"]:
        return "rejected", [f"early reject: profit factor {pf:.2f} < {early['max_profit_factor']} after {m['trades']} trades"]
    enough = m["trades"] >= cfg["min_closed_trades"] and m["days"] >= cfg["min_days"]
    if not enough:
        return "collecting", [f"{m['trades']}/{cfg['min_closed_trades']} closed trades, {m['days']:.1f}/{cfg['min_days']} days"]
    if pf is None or pf < cfg["reject_at_min_trades"]["max_profit_factor"] or m["net_profit"] <= 0:
        return "rejected", [f"at {m['trades']} trades: net profit {m['net_profit']:.2f}, profit factor "
                            f"{'n/a' if pf is None else format(pf, '.2f')}"]
    bar = cfg["approve"]
    checks = [
        (pf >= bar["min_profit_factor"], f"profit factor {pf:.2f} >= {bar['min_profit_factor']}"),
        (m["expectancy_pct"] >= bar["min_expectancy_pct"], f"expectancy {m['expectancy_pct']:.2f}% per trade >= {bar['min_expectancy_pct']}%"),
        (m["prob_mean_positive"] >= bar["min_prob_mean_positive"], f"P(mean trade > 0) {m['prob_mean_positive']:.2f} >= {bar['min_prob_mean_positive']}"),
        (m["max_drawdown_pct"] <= bar["max_drawdown_pct_of_wallet"], f"drawdown {m['max_drawdown_pct']:.1f}% <= {bar['max_drawdown_pct_of_wallet']}% of wallet"),
    ]
    if bar["require_profit_excluding_best_trade_positive"]:
        checks.append((m["net_profit_excl_best"] > 0, f"profit without the best trade {m['net_profit_excl_best']:.2f} > 0"))
    observed = (execution or {}).get("observed_entry_cost_per_side_mean")
    if observed is not None:
        limit = costs.get_scenario("conservative").effective_fee_per_side * bar["max_observed_entry_cost_per_side_vs_conservative"]
        checks.append((observed <= limit, f"observed entry cost {observed:.3%}/side <= {limit:.3%} (conservative scenario)"))
    for ok, text in checks:
        reasons.append(("pass: " if ok else "FAIL: ") + text)
    return ("approved_for_review" if all(ok for ok, _ in checks) else "collecting"), reasons


def _wallet(hypothesis_id: str, key: str, cfg: dict, root: Path) -> float:
    overlay = root / forward.overlay_path(hypothesis_id, key)
    if overlay.is_file():
        try:
            return float(json.loads(overlay.read_text(encoding="utf-8")).get("dry_run_wallet", cfg["default_wallet_quote"]))
        except (ValueError, OSError):
            pass
    return float(cfg["default_wallet_quote"])


def evaluate_hypothesis(hypothesis_id: str, cfg: dict | None = None, root: Path = ROOT) -> dict:
    """Pool the closed trades of every pair bot of a frozen hypothesis and judge them together."""
    cfg = cfg or load_config()
    pooled, per_pair, wallet, raw_trades, raw_orders = [], {}, 0.0, [], []
    for key in forward.pair_keys(hypothesis_id, root):
        trades, orders = forward.read_database(root / forward.database_path(hypothesis_id, key))
        bot_wallet = _wallet(hypothesis_id, key, cfg, root)
        closed = forward.closed_as_backtest_trades(trades)
        wallet += bot_wallet
        pooled += closed
        raw_trades += trades
        raw_orders += orders
        pair = forward.PAIR_KEYS.get(key, key)
        per_pair[pair] = metrics(closed, bot_wallet, cfg)
    pooled_metrics = metrics(pooled, wallet, cfg)
    execution = forward.execution_quality(raw_trades, raw_orders) if raw_trades else None
    state, reasons = verdict(pooled_metrics, cfg, execution)
    return {"hypothesis": hypothesis_id, "verdict": state, "reasons": reasons, "pooled": pooled_metrics,
            "per_pair": per_pair, "wallet": wallet}


def frozen_hypotheses(root: Path = ROOT) -> list[str]:
    return sorted(p.name.split("-freeze.json")[0] for p in (root / "research" / "forward").glob("H-*-freeze.json"))


def _f(value, digits=2, suffix="") -> str:
    if value is None:
        return "–"
    if value == float("inf"):
        return "∞"
    return f"{value:.{digits}f}{suffix}"


def render(results: list[dict], cfg: dict) -> str:
    lines = ["# Veredito do dry-run (por número de trades e por todas as métricas)", "",
             "Regra: lab/config/dryrun.json (decisão do dono em 10/11/2026). Aprovação aqui = vale uma análise humana para dinheiro real, "
             "nunca uma ordem. O holdout formal (>= 2027-04-21) continua separado e inalterado.", "",
             f"Mínimo para decidir: {cfg['min_closed_trades']} trades fechados e {cfg['min_days']} dias; reprova cedo com "
             f"{cfg['early_reject']['min_closed_trades']}+ trades e fator de lucro < {cfg['early_reject']['max_profit_factor']}.", "",
             "| Hipótese | Veredito | Trades | Dias | Acerto | Payoff | Fator de lucro | Expectativa/trade | Lucro (USDT) | Sem o melhor | Drawdown | P(média>0) |",
             "|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for r in results:
        m = r["pooled"]
        win = None if m["win_rate"] is None else 100 * m["win_rate"]
        lines.append(f"| {r['hypothesis']} | {r['verdict']} | {m['trades']} | {_f(m['days'], 1)} | {_f(win, 1, '%')} | {_f(m['payoff'])} | "
                     f"{_f(m['profit_factor'])} | {_f(m['expectancy_pct'], 2, '%')} | {_f(m['net_profit'])} | {_f(m['net_profit_excl_best'])} | "
                     f"{_f(m['max_drawdown_pct'], 1, '%')} | {_f(m['prob_mean_positive'])} |")
    lines.append("")
    for r in results:
        lines += [f"## {r['hypothesis']}: {r['verdict']}", *(f"- {reason}" for reason in r["reasons"]), ""]
        if r["verdict"] == "rejected":
            lines += ["Recomendação: parar este bot (os números dizem que a vantagem não existe).", ""]
    return "\n".join(lines)


def run_and_commit(pipeline) -> str:
    """Evaluate every frozen hypothesis, write the report, commit it. Used by `python -m lab.pipeline dryrun`."""
    cfg = load_config()
    results = [evaluate_hypothesis(h, cfg, pipeline.root) for h in frozen_hypotheses(pipeline.root)]
    path = pipeline.root / REPORT
    path.write_text(render(results, cfg), encoding="utf-8")
    pipeline._commit([REPORT], "dry-run verdicts (by trades and metrics): " + ", ".join(f"{r['hypothesis']} {r['verdict']}" for r in results))
    return str(path)
