"""Metrics of a B3 backtest, in BRL per contract, from its trade list.

Gate THRESHOLDS are not here: they go to lab/config/gates_b3.json after the owner approves the B3
protocol (plan, section 7). This module only measures. Income tax is estimated separately and never
mixed into the net result (20% of the positive monthly day-trade net, after carrying losses forward;
the 1% withheld at source is an advance on that tax, not an extra cost).
"""

from __future__ import annotations

import math

import pandas as pd

from b3.calendar import SP_TZ
from lab.stats import probabilistic_sharpe, sharpe

DAY_TRADE_TAX_RATE = 0.20


def _max_drawdown(cum: pd.Series, capital: float) -> tuple[float, float]:
    """(max drawdown in BRL, as % of the running peak of capital + cumulative net)."""
    equity = capital + cum
    peak = equity.cummax().clip(lower=capital)
    dd = peak - equity
    if dd.empty:
        return 0.0, 0.0
    i = dd.idxmax()
    return float(dd.max()), float(100.0 * dd.max() / peak[i]) if peak[i] > 0 else math.inf


def monthly_tax(trades: pd.DataFrame, rate: float = DAY_TRADE_TAX_RATE) -> pd.DataFrame:
    """Estimated day-trade income tax per month (losses carried forward), for the report only."""
    if trades.empty:
        return pd.DataFrame(columns=["month", "net_brl", "taxable_brl", "tax_brl"])
    months = pd.to_datetime(trades["exit_time"], utc=True).dt.tz_convert(SP_TZ).dt.strftime("%Y-%m")
    net = trades.groupby(months)["net_brl"].sum().sort_index()
    carry, rows = 0.0, []
    for month, value in net.items():
        base = value + carry
        if base > 0:
            rows.append((month, value, base, rate * base))
            carry = 0.0
        else:
            rows.append((month, value, 0.0, 0.0))
            carry = base
    return pd.DataFrame(rows, columns=["month", "net_brl", "taxable_brl", "tax_brl"])


def summarise(trades: pd.DataFrame, *, capital_brl: float, sessions: int | None = None) -> dict:
    """Headline metrics. `sessions` = trading sessions in the tested window (for per-year rates)."""
    n = len(trades)
    out: dict = {"trades": n, "capital_brl": capital_brl}
    if n == 0:
        return out | {"net_brl": 0.0}
    t = trades.sort_values("exit_time").reset_index(drop=True)
    net = t["net_brl"]
    wins, losses = net[net > 0], net[net <= 0]
    cum = net.cumsum()
    dd_brl, dd_pct = _max_drawdown(cum, capital_brl)
    best = net.idxmax()
    local_exit = pd.to_datetime(t["exit_time"], utc=True).dt.tz_convert(SP_TZ)
    daily = t.groupby(local_exit.dt.date)["net_brl"].sum()
    years = (sessions / 250.0) if sessions else None
    streak = longest = 0
    for v in net:
        streak = streak + 1 if v <= 0 else 0
        longest = max(longest, streak)
    hold = (pd.to_datetime(t["exit_time"]) - pd.to_datetime(t["entry_time"])).dt.total_seconds() / 60
    out |= {
        "net_brl": float(net.sum()),
        "gross_brl": float(t["gross_brl"].sum()),
        "cost_brl": float(t["cost_brl"].sum()),
        "net_excl_best_trade_brl": float(net.drop(index=best).sum()),
        "best_trade_brl": float(net[best]),
        "expectancy_brl": float(net.mean()),
        "expectancy_points": float(t["points"].mean()),
        "gross_points_per_trade": float((t["gross_brl"] / t["contracts"]).mean()),
        "win_rate_pct": 100.0 * len(wins) / n,
        "avg_win_brl": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_brl": float(losses.mean()) if len(losses) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else math.inf,
        "max_drawdown_brl": dd_brl,
        "max_drawdown_pct_of_capital": dd_pct,
        "return_pct_of_capital": 100.0 * float(net.sum()) / capital_brl,
        "longest_losing_streak": longest,
        "median_hold_min": float(hold.median()),
        "days_traded": int(len(daily)),
        "daily_sharpe": sharpe(daily.to_numpy()) if len(daily) > 2 else math.nan,
        "prob_sharpe_gt_0": probabilistic_sharpe(daily.to_numpy()) if len(daily) > 2 else math.nan,
        "long_trades": int((t["side"] == "long").sum()),
        "short_trades": int((t["side"] == "short").sum()),
        "net_long_brl": float(net[t["side"] == "long"].sum()),
        "net_short_brl": float(net[t["side"] == "short"].sum()),
        "exit_reasons": t["exit_reason"].value_counts().to_dict(),
        "estimated_tax_brl": float(monthly_tax(t)["tax_brl"].sum()),
    }
    if years:
        out["trades_per_year"] = n / years
        out["net_brl_per_year"] = float(net.sum()) / years
    return out


def by_year(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["year", "trades", "net_brl", "win_rate_pct"])
    year = pd.to_datetime(trades["exit_time"], utc=True).dt.tz_convert(SP_TZ).dt.year
    g = trades.groupby(year)["net_brl"]
    return pd.DataFrame({"trades": g.size(), "net_brl": g.sum(),
                         "win_rate_pct": g.apply(lambda s: 100.0 * (s > 0).mean())}).reset_index(names="year")
