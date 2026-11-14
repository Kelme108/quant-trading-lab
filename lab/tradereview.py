"""Trade-level review of an exported backtest: where the money is made and lost, trade by trade.

Pure functions over the trade list exactly as Freqtrade exports it (open_date, close_date, open_rate, close_rate,
min_rate, max_rate, profit_ratio, profit_abs, stake_amount, fee_open, fee_close, exit_reason, trade_duration in
minutes). No I/O, no candles: the price extremes of each trade come from the export itself.

Nothing here decides anything. It describes the failure mechanism so that a NEW hypothesis can name it; win rate is
reported like every other number and is never a criterion.

MAE  (maximum adverse excursion)  = min_rate / open_rate - 1  (worst unrealised move, before costs)
MFE  (maximum favourable excursion) = max_rate / open_rate - 1  (best unrealised move, before costs)
Give-back of a winner = MFE - profit_ratio: how much of the best move was returned before the exit.
"""

from __future__ import annotations

import math
from statistics import median

import pandas as pd

# (label, lower bound inclusive in hours, upper bound exclusive in hours)
DURATION_BUCKETS = (
    ("< 3 h", 0.0, 3.0),
    ("3 h a 1 dia", 3.0, 24.0),
    ("1 a 7 dias", 24.0, 24.0 * 7),
    ("7 a 30 dias", 24.0 * 7, 24.0 * 30),
    ("> 30 dias", 24.0 * 30, math.inf),
)
QUICK_REENTRY_HOURS = 24.0
SHORT_TRADE_HOURS = 3.0
GREEN_BEFORE_LOSS = 0.02  # a losing trade that had been 2% in profit before it lost


def _num(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _ts(value) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def _hours(trade: dict) -> float:
    minutes = _num(trade.get("trade_duration"))
    if minutes is not None:
        return minutes / 60.0
    return (_ts(trade["close_date"]) - _ts(trade["open_date"])).total_seconds() / 3600.0


def excursions(trade: dict) -> tuple[float | None, float | None]:
    """(MAE, MFE) as ratios of the entry price, or (None, None) when the export has no price extremes."""
    open_rate, low, high = _num(trade.get("open_rate")), _num(trade.get("min_rate")), _num(trade.get("max_rate"))
    if not open_rate or low is None or high is None:
        return None, None
    if trade.get("is_short"):           # a short is hurt by the high and helped by the low
        return min(1.0 - high / open_rate, 0.0), max(1.0 - low / open_rate, 0.0)
    return min(low / open_rate - 1.0, 0.0), max(high / open_rate - 1.0, 0.0)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _share(part: float, total: float) -> float | None:
    return part / total if total > 0 else None


def exit_reason_table(trades: list[dict]) -> list[dict]:
    """One row per exit reason, largest group first. `share_of_net` is None when the total is not positive."""
    total = sum(float(t["profit_abs"]) for t in trades)
    groups: dict[str, list[dict]] = {}
    for trade in trades:
        groups.setdefault(str(trade.get("exit_reason") or "—"), []).append(trade)
    rows = []
    for reason, items in groups.items():
        net = sum(float(t["profit_abs"]) for t in items)
        wins = sum(1 for t in items if float(t["profit_abs"]) > 0)
        rows.append({
            "exit_reason": reason, "trades": len(items), "share_of_trades": len(items) / len(trades) if trades else None,
            "net_profit_abs": net, "share_of_net": _share(net, total),
            "mean_profit_pct": sum(float(t["profit_ratio"]) for t in items) / len(items) * 100,
            "winrate": wins / len(items), "mean_hours": sum(_hours(t) for t in items) / len(items),
        })
    return sorted(rows, key=lambda r: -r["trades"])


def duration_table(trades: list[dict]) -> list[dict]:
    rows = []
    for label, low, high in DURATION_BUCKETS:
        items = [t for t in trades if low <= _hours(t) < high]
        if not items:
            rows.append({"bucket": label, "trades": 0, "net_profit_abs": 0.0, "mean_profit_pct": None, "winrate": None})
            continue
        rows.append({
            "bucket": label, "trades": len(items), "net_profit_abs": sum(float(t["profit_abs"]) for t in items),
            "mean_profit_pct": sum(float(t["profit_ratio"]) for t in items) / len(items) * 100,
            "winrate": sum(1 for t in items if float(t["profit_abs"]) > 0) / len(items),
        })
    return rows


def excursion_summary(trades: list[dict]) -> dict:
    """MAE/MFE and give-back. Winners and losers are described separately because they fail differently."""
    winners, losers = [], []
    for trade in trades:
        mae, mfe = excursions(trade)
        if mae is None:
            continue
        (winners if float(trade["profit_ratio"]) > 0 else losers).append((trade, mae, mfe))
    if not winners and not losers:
        return {"available": False}
    giveback = [mfe - float(t["profit_ratio"]) for t, _, mfe in winners]
    capture = [float(t["profit_ratio"]) / mfe for t, _, mfe in winners if mfe > 0]
    green_losers = [1 for _, _, mfe in losers if mfe >= GREEN_BEFORE_LOSS]
    return {
        "available": True, "winners": len(winners), "losers": len(losers),
        "winner_median_mfe_pct": median([m for _, _, m in winners]) * 100 if winners else None,
        "winner_median_mae_pct": median([m for _, m, _ in winners]) * 100 if winners else None,
        "winner_mean_giveback_pct": _mean(giveback) * 100 if giveback else None,
        "winner_median_capture": median(capture) if capture else None,
        "loser_median_mae_pct": median([m for _, m, _ in losers]) * 100 if losers else None,
        "loser_median_mfe_pct": median([m for _, _, m in losers]) * 100 if losers else None,
        "losers_green_before_loss": len(green_losers),
        "losers_green_before_loss_share": len(green_losers) / len(losers) if losers else None,
    }


def cost_share(trades: list[dict]) -> dict:
    """Fees paid, and what share of the profit before costs they took. None when the export lacks stake or fees."""
    fees = 0.0
    for trade in trades:
        stake, fee_open, fee_close = _num(trade.get("stake_amount")), _num(trade.get("fee_open")), _num(trade.get("fee_close"))
        if stake is None or fee_open is None or fee_close is None:
            return {"fees_paid_abs": None, "gross_profit_abs": None, "fee_share_of_gross": None}
        fees += stake * fee_open + stake * (1.0 + float(trade["profit_ratio"])) * fee_close
    net = sum(float(t["profit_abs"]) for t in trades)
    gross = net + fees
    return {"fees_paid_abs": fees, "gross_profit_abs": gross, "fee_share_of_gross": _share(fees, gross)}


def short_and_quick(trades: list[dict]) -> dict:
    """Very short trades and re-entries soon after an exit (whipsaw signature)."""
    ordered = sorted(trades, key=lambda t: str(t["open_date"]))
    short = [t for t in ordered if _hours(t) < SHORT_TRADE_HOURS]
    quick = []
    for previous, current in zip(ordered, ordered[1:]):
        gap = (_ts(current["open_date"]) - _ts(previous["close_date"])).total_seconds() / 3600.0
        if gap < QUICK_REENTRY_HOURS:
            quick.append(current)

    def describe(items: list[dict]) -> dict:
        return {"trades": len(items), "net_profit_abs": sum(float(t["profit_abs"]) for t in items),
                "winrate": sum(1 for t in items if float(t["profit_abs"]) > 0) / len(items) if items else None}

    return {"short_hours": SHORT_TRADE_HOURS, "short": describe(short),
            "quick_reentry_hours": QUICK_REENTRY_HOURS, "quick_reentry": describe(quick)}


def concentration(trades: list[dict]) -> dict:
    profits = sorted((float(t["profit_abs"]) for t in trades), reverse=True)
    total = sum(profits)
    by_year: dict[str, float] = {}
    for trade in trades:
        year = str(trade["close_date"])[:4]
        by_year[year] = by_year.get(year, 0.0) + float(trade["profit_abs"])
    return {
        "top1_share": _share(sum(profits[:1]), total), "top5_share": _share(sum(profits[:5]), total),
        "top10_share": _share(sum(profits[:10]), total), "net_profit_abs": total,
        "profit_excl_best_abs": total - profits[0] if profits else None,
        "net_by_year": dict(sorted(by_year.items())),
    }


def review(trades: list[dict]) -> dict:
    """Everything above for one pair's trade list."""
    if not trades:
        return {"trades": 0}
    return {
        "trades": len(trades),
        "net_profit_abs": sum(float(t["profit_abs"]) for t in trades),
        "exit_reasons": exit_reason_table(trades), "durations": duration_table(trades),
        "excursions": excursion_summary(trades), "costs": cost_share(trades),
        "short_and_quick": short_and_quick(trades), "concentration": concentration(trades),
    }


def _p(value, digits=1, suffix="%", scale=1.0) -> str:
    return "–" if value is None else f"{value * scale:.{digits}f}{suffix}"


def render_markdown(title: str, source: str, by_pair: dict[str, dict]) -> str:
    """A readable report. Each table states its source file."""
    lines = [f"# {title}", "", f"Fonte dos trades: {source}. Janela: exploração. Cenário de custo: base.", ""]
    for pair, rv in by_pair.items():
        lines += [f"## {pair}", ""]
        if not rv.get("trades"):
            lines += ["Sem trades.", ""]
            continue
        lines += [f"Trades: {rv['trades']}; lucro líquido: {rv['net_profit_abs']:.2f}.", "",
                  "### Por motivo de saída", "",
                  "| Saída | Trades | Lucro líquido | % do lucro | Retorno médio | Win rate | Duração média |",
                  "|---|--:|--:|--:|--:|--:|--:|"]
        for r in rv["exit_reasons"]:
            lines.append(f"| {r['exit_reason']} | {r['trades']} | {r['net_profit_abs']:.2f} | {_p(r['share_of_net'], 0, '%', 100)} | "
                         f"{r['mean_profit_pct']:.2f}% | {_p(r['winrate'], 0, '%', 100)} | {r['mean_hours']:.1f} h |")
        lines += ["", "### Por duração", "", "| Faixa | Trades | Lucro líquido | Retorno médio | Win rate |", "|---|--:|--:|--:|--:|"]
        for r in rv["durations"]:
            lines.append(f"| {r['bucket']} | {r['trades']} | {r['net_profit_abs']:.2f} | "
                         f"{'–' if r['mean_profit_pct'] is None else format(r['mean_profit_pct'], '.2f') + '%'} | {_p(r['winrate'], 0, '%', 100)} |")
        ex = rv["excursions"]
        lines += ["", "### Excursões (antes de custos)", ""]
        if ex.get("available"):
            lines += [
                f"- Vencedores ({ex['winners']}): MFE mediano {_p(ex['winner_median_mfe_pct'], 1, '%')}, MAE mediano {_p(ex['winner_median_mae_pct'], 1, '%')}, "
                f"devolução média do melhor ponto {_p(ex['winner_mean_giveback_pct'], 1, '%')}, captura mediana {_p(ex['winner_median_capture'], 2, '', 1)}.",
                f"- Perdedores ({ex['losers']}): MAE mediano {_p(ex['loser_median_mae_pct'], 1, '%')}, MFE mediano {_p(ex['loser_median_mfe_pct'], 1, '%')}; "
                f"{ex['losers_green_before_loss']} ({_p(ex['losers_green_before_loss_share'], 0, '%', 100)}) já estavam ≥ 2% no lucro antes de perder.",
            ]
        else:
            lines.append("- O export não traz os extremos de preço.")
        cs, sq, cc = rv["costs"], rv["short_and_quick"], rv["concentration"]
        lines += ["", "### Custo, trades curtos e concentração", "",
                  f"- Taxas pagas: {_p(cs['fees_paid_abs'], 2, '', 1)}; {_p(cs['fee_share_of_gross'], 0, '%', 100)} do lucro antes de custos.",
                  f"- Trades < {sq['short_hours']:.0f} h: {sq['short']['trades']} (lucro {sq['short']['net_profit_abs']:.2f}); "
                  f"reentradas em < {sq['quick_reentry_hours']:.0f} h: {sq['quick_reentry']['trades']} (lucro {sq['quick_reentry']['net_profit_abs']:.2f}).",
                  f"- Maior trade = {_p(cc['top1_share'], 0, '%', 100)} do lucro; top 5 = {_p(cc['top5_share'], 0, '%', 100)}; top 10 = {_p(cc['top10_share'], 0, '%', 100)}; "
                  f"lucro sem o melhor = {_p(cc['profit_excl_best_abs'], 2, '', 1)}.",
                  "- Lucro por ano de fechamento: " + ", ".join(f"{y}: {v:.1f}" for y, v in cc["net_by_year"].items()) + ".", ""]
    return "\n".join(lines)
