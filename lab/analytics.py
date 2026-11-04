"""Strategy analytics for the portal: pure functions over exported backtest trades (no I/O, no state).

Everything here is derived from what Freqtrade exported (trade lists and the stats it computed). Nothing is
estimated beyond what is labelled, and a metric that cannot be computed is None, never a placeholder number.

Units: `profit_ratio` is a fraction per trade (0.02 = +2%), `profit_abs` is in the quote currency (USDT) of a
simulated wallet. Origin of every number: backtest (simulated). The lab has no real or dry-run trades yet.

The leaderboard score is NOT a win-rate ranking. It is a transparent 0-100 blend, shown with its parts:
    rentabilidade 30 + risco 25 + amostra 20 + consistência 25, then capped: at 40 when any pair has < MIN_TRADES
    trades, and at 60 when the gates rejected any pair (the gates stay authoritative; the score never overrides them).
See `score_parts` for the exact formulas.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime

MIN_TRADES = 30            # per pair: same bar as lab/config/gates.json minimum_trades
DD_GATE_PCT = 25.0         # gates.json max_drawdown
HIST_BINS = 21
GATE_REJECT_CAP = 60.0
MIN_LAST_THIRD = 20        # trades needed in the last third before "worsening" is called
SCORE_WEIGHTS = {"profit": 30, "risk": 25, "sample": 20, "consistency": 25}


def _num(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson interval for a win rate (fractions). None when there are no trades."""
    if n <= 0:
        return None
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(str(ts))


def streaks(profits: list[float]) -> dict:
    """Longest win run, longest loss run and the run the series ends in (+n win, -n loss)."""
    best_win = best_loss = run = 0
    last = 0
    for p in profits:
        sign = 1 if p > 0 else -1 if p < 0 else 0
        if sign == 0:
            run, last = 0, 0
            continue
        run = run + 1 if sign == last else 1
        last = sign
        if sign > 0:
            best_win = max(best_win, run)
        else:
            best_loss = max(best_loss, run)
    return {"max_win": best_win, "max_loss": best_loss, "current": last * run if last else 0}


def histogram(values: list[float], bins: int = HIST_BINS) -> dict | None:
    """Symmetric-around-zero histogram of per-trade returns (percent) for the distribution chart."""
    if not values:
        return None
    span = max(abs(min(values)), abs(max(values)), 1e-9)
    # bins are centred so that zero sits in the middle bin
    half = bins // 2
    width = span / (half + 0.5)
    counts = [0] * bins
    for v in values:
        index = int(math.floor(v / width + 0.5)) + half
        counts[max(0, min(bins - 1, index))] += 1
    edges = [(i - half - 0.5) * width for i in range(bins + 1)]
    return {"edges": edges, "counts": counts}


def trade_metrics(trades: list[dict], starting_balance: float) -> dict:
    """All per-run metrics that follow from a trade list. `trades` need open_date, close_date, profit_ratio, profit_abs."""
    ordered = sorted(trades, key=lambda t: str(t["close_date"]))
    n = len(ordered)
    out: dict = {"trades": n, "starting_balance": _num(starting_balance)}
    if n == 0:
        return {**out, "winrate": None, "profit_factor": None, "net_profit_abs": 0.0, "roi_pct": 0.0}
    abs_ = [float(t["profit_abs"]) for t in ordered]
    ratio = [float(t["profit_ratio"]) for t in ordered]
    wins = [x for x in abs_ if x > 0]
    losses = [x for x in abs_ if x < 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    net = sum(abs_)
    interval = wilson_interval(len(wins), n)
    win_ratio = [r for r in ratio if r > 0]
    loss_ratio = [r for r in ratio if r < 0]
    avg_win = sum(win_ratio) / len(win_ratio) * 100 if win_ratio else None
    avg_loss = sum(loss_ratio) / len(loss_ratio) * 100 if loss_ratio else None
    best = max(abs_)
    third = max(1, n // 3)
    first, last = ratio[: n - third], ratio[n - third:]
    durations = [_num(t.get("trade_duration")) for t in ordered]
    durations = [d for d in durations if d is not None]
    monthly: dict[str, float] = defaultdict(float)
    for t, p in zip(ordered, abs_):
        monthly[str(t["close_date"])[:7]] += p
    reasons: dict[str, int] = defaultdict(int)
    for t in ordered:
        reasons[str(t.get("exit_reason") or "—")] += 1
    fees = 0.0
    fee_known = True
    for t in ordered:
        stake, fo, fc = _num(t.get("stake_amount")), _num(t.get("fee_open")), _num(t.get("fee_close"))
        if stake is None or fo is None or fc is None:
            fee_known = False
            break
        fees += stake * fo + stake * (1 + float(t["profit_ratio"])) * fc
    out.update(
        {
            "wins": len(wins), "losses": len(losses),
            "winrate": len(wins) / n,
            "winrate_ci": list(interval) if interval else None,
            "profit_factor": gross_win / gross_loss if gross_loss > 0 else None,
            "profit_factor_note": None if gross_loss > 0 else "sem trades perdedores",
            "gross_profit_abs": gross_win, "gross_loss_abs": -gross_loss,
            "net_profit_abs": net,
            "roi_pct": net / starting_balance * 100 if starting_balance else None,
            "expectancy_abs": net / n,
            "expectancy_pct": sum(ratio) / n * 100,
            "avg_win_pct": avg_win, "avg_loss_pct": avg_loss,
            "payoff": avg_win / abs(avg_loss) if avg_win is not None and avg_loss else None,
            "best_trade_abs": best, "worst_trade_abs": min(abs_),
            "profit_excl_best_abs": net - best,
            "top_trade_share": best / net if net > 0 else None,
            "streaks": streaks(abs_),
            "avg_duration_h": sum(durations) / len(durations) / 60 if durations else None,
            "exit_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
            "histogram": histogram([r * 100 for r in ratio]),
            "monthly": [[k, v / starting_balance * 100 if starting_balance else None] for k, v in sorted(monthly.items())],
            "fees_paid_abs": fees if fee_known else None,
            "expectancy_first_pct": sum(first) / len(first) * 100 if first else None,
            "expectancy_last_pct": sum(last) / len(last) * 100 if last else None,
            "trades_last": len(last),
            "period": [str(ordered[0]["open_date"]), str(ordered[-1]["close_date"])],
        }
    )
    return out


def cumulative_profit(trades: list[dict]) -> list[list[float]]:
    """[[epoch_ms, cumulative profit_abs]] at every trade close, summed over whatever pairs are in `trades`."""
    points, total = [], 0.0
    for t in sorted(trades, key=lambda t: str(t["close_date"])):
        total += float(t["profit_abs"])
        points.append([_parse(t["close_date"]).timestamp() * 1000, total])
    return points


def downsample(points: list[list[float]], limit: int = 160) -> list[list[float]]:
    """Keeps the first and last point and an even subset in between (the shape of a curve, not its detail)."""
    if len(points) <= limit:
        return points
    step = (len(points) - 1) / (limit - 1)
    return [points[round(i * step)] for i in range(limit)]


# --- score and flags ---------------------------------------------------------------------------


def score_parts(row: dict) -> dict:
    """The four components (0..1) behind the evidence score, from a strategy row's own numbers."""
    pf = row.get("profit_factor")
    stress_ok = row.get("roi_stress_pct") is not None and row["roi_stress_pct"] > 0
    profit = _clamp(((pf if pf is not None else 3.0) - 1.0) / 1.0) * (1.0 if stress_ok else 0.5) if (row.get("roi_pct") or 0) > 0 else 0.0
    dd = row.get("max_dd_pct")
    dd_c = _clamp(1 - ((dd if dd is not None else 40.0) - 10.0) / 30.0)
    roi = row.get("roi_pct")
    ratio_c = _clamp((roi / max(dd, 1.0)) / 3.0) if roi is not None and dd is not None and roi > 0 else 0.0
    risk = 0.5 * dd_c + 0.5 * ratio_c
    min_pair = row.get("min_trades_pair") or 0
    sample = 0.6 * _clamp(min_pair / MIN_TRADES) + 0.4 * _clamp((row.get("trades") or 0) / 100)
    n_pairs = max(1, row.get("n_pairs") or 1)
    consistency = (
        0.4 * (row.get("pairs_positive", 0) / n_pairs)
        + 0.3 * (row.get("pairs_excl_best_positive", 0) / n_pairs)
        + 0.3 * (row.get("positive_year_share") if row.get("positive_year_share") is not None else 0.0)
    )
    return {"profit": profit, "risk": risk, "sample": sample, "consistency": consistency}


def evidence_score(row: dict) -> tuple[float, dict]:
    parts = score_parts(row)
    score = sum(SCORE_WEIGHTS[k] * parts[k] for k in SCORE_WEIGHTS)
    capped = (row.get("min_trades_pair") or 0) < MIN_TRADES
    if capped:
        score = min(score, 40.0)
    gate_capped = bool(row.get("gates_any_rejected"))
    if gate_capped:
        score = min(score, GATE_REJECT_CAP)
    return round(score, 1), {**{k: round(v, 3) for k, v in parts.items()}, "capped_by_sample": capped, "capped_by_gates": gate_capped}


def flags(row: dict, other_stage: dict | None = None) -> list[dict]:
    """Plain-language signals, each carrying the numbers that triggered it. level: good | warn | bad | info."""
    out: list[dict] = []

    def add(level: str, key: str, text: str) -> None:
        out.append({"level": level, "key": key, "text": text})

    n_pairs = row.get("n_pairs") or 0
    if row.get("gates_all_pass"):
        add("good", "gates", "Passou nos gates em todos os pares desta etapa")
    elif row.get("gates_any_rejected"):
        add("bad", "gates_rejected", "Rejeitada pelos gates em pelo menos um par")
    min_pair = row.get("min_trades_pair")
    if min_pair is not None and min_pair < MIN_TRADES:
        add("warn", "sample", f"Amostra pequena: {min_pair} trades no par com menos operações (mínimo {MIN_TRADES}); resultados pouco confiáveis")
    dd = row.get("max_dd_pct")
    if dd is not None and dd > DD_GATE_PCT:
        add("bad", "drawdown", f"Drawdown de {dd:.1f}% acima do limite de {DD_GATE_PCT:.0f}%")
    roi = row.get("roi_pct")
    if roi is not None and roi <= 0:
        add("bad", "loss", f"Prejuízo no cenário base (ROI {roi:+.1f}%)")
    if row.get("pairs_excl_best_positive", n_pairs) < n_pairs and (roi or 0) > 0:
        bad_pairs = n_pairs - row.get("pairs_excl_best_positive", n_pairs)
        add("bad", "one_trade", f"Dependente de um único trade em {bad_pairs} de {n_pairs} pares: sem o melhor trade o lucro some")
    stress = row.get("roi_stress_pct")
    if stress is not None and roi is not None and roi > 0 and stress <= 0:
        add("warn", "costs", f"Sensível a custos: lucro no cenário base ({roi:+.1f}%), prejuízo no estresse ({stress:+.1f}%)")
    pos, nn = row.get("pairs_positive", 0), n_pairs
    if nn >= 2 and 0 < pos < nn:
        add("warn", "pairs", f"Inconsistente entre pares: lucro em {pos} de {nn}")
    elif nn >= 2 and pos == nn and (roi or 0) > 0:
        add("good", "pairs_ok", f"Lucrativa em todos os {nn} pares")
    first, last = row.get("expectancy_first_pct"), row.get("expectancy_last_pct")
    if first is not None and last is not None and (row.get("trades_last") or 0) >= MIN_LAST_THIRD and first > 0 and last < 0.5 * first:
        add("warn", "worsening", f"Piorando: expectativa por trade caiu de {first:+.2f}% (primeiros 2/3) para {last:+.2f}% (último 1/3, {row.get('trades_last')} trades)")
    if other_stage and row.get("stage") == "exploration":
        v_roi, v_pf = other_stage.get("roi_pct"), other_stage.get("profit_factor")
        pf = row.get("profit_factor")
        if roi is not None and v_roi is not None and roi > 0 and (v_roi <= 0 or (pf and v_pf and v_pf < 0.5 * pf)):
            add("warn", "overfit", f"Possível overfitting: ROI {roi:+.1f}% na exploração contra {v_roi:+.1f}% na validação")
    if row.get("stage") == "exploration" and other_stage is None and row.get("gates_all_pass"):
        add("info", "no_validation", "Ainda sem validação: o resultado é só da amostra de exploração")
    return out
