import pandas as pd
import pytest

from b3.metrics import by_year, monthly_tax, summarise


def trades(nets, start="2026-03-02 13:00", sides=None):
    t0 = pd.Timestamp(start, tz="UTC")
    rows = []
    for i, n in enumerate(nets):
        rows.append({"symbol": "WINZ26", "side": (sides or ["long"] * len(nets))[i], "contracts": 1.0,
                     "entry_time": t0 + pd.Timedelta(days=i), "exit_time": t0 + pd.Timedelta(days=i, minutes=30),
                     "points": n * 5, "gross_brl": n + 0.5, "cost_brl": 0.5, "net_brl": float(n),
                     "exit_reason": "x"})
    return pd.DataFrame(rows)


def test_headline_metrics():
    m = summarise(trades([100, -50, 30, -20, 200], sides=["long", "short", "long", "short", "long"]),
                  capital_brl=10_000, sessions=250)
    assert m["trades"] == 5 and m["net_brl"] == pytest.approx(260)
    assert m["net_excl_best_trade_brl"] == pytest.approx(60)
    assert m["win_rate_pct"] == pytest.approx(60)
    assert m["profit_factor"] == pytest.approx(330 / 70)
    assert m["max_drawdown_brl"] == pytest.approx(50)
    assert m["trades_per_year"] == pytest.approx(5)
    assert (m["long_trades"], m["short_trades"], m["net_short_brl"]) == (3, 2, -70)
    assert m["longest_losing_streak"] == 1


def test_empty_trade_list():
    assert summarise(pd.DataFrame(), capital_brl=10_000) == {"trades": 0, "capital_brl": 10_000, "net_brl": 0.0}


def test_tax_carries_losses_forward_within_day_trade():
    t = pd.concat([trades([-300], "2026-03-10 13:00"), trades([500], "2026-04-10 13:00"),
                   trades([100], "2026-05-10 13:00")], ignore_index=True)
    tax = monthly_tax(t).set_index("month")
    assert tax.loc["2026-03", "tax_brl"] == 0
    assert tax.loc["2026-04", "taxable_brl"] == pytest.approx(200)     # 500 - 300 carried
    assert tax.loc["2026-04", "tax_brl"] == pytest.approx(40)
    assert tax.loc["2026-05", "tax_brl"] == pytest.approx(20)
    assert list(by_year(t)["trades"]) == [3]
