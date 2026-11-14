import pytest

from b3.costs import COSTS, REQUIRED_SCENARIOS, cost_table, get_cost
from b3.instruments import INSTRUMENTS, check_server_spec, instrument_for
from live.core.models import SymbolSpec


def test_published_specs():
    assert INSTRUMENTS["WIN"].tick_value_brl == pytest.approx(1.0)
    assert INSTRUMENTS["WDO"].tick_value_brl == pytest.approx(5.0)
    assert instrument_for("WIN$N").root == "WIN" and instrument_for("wdoz26").root == "WDO"
    with pytest.raises(ValueError):
        instrument_for("PETR4")


def test_server_spec_cross_check():
    assert check_server_spec(SymbolSpec("WINZ26", 5.0, 1.0)) == []
    assert check_server_spec(SymbolSpec("WDOZ26", 0.5, 5.0)) == []
    problems = check_server_spec(SymbolSpec("WINZ26", 5.0, 0.2))
    assert len(problems) == 1 and "tick_value" in problems[0]


def test_round_trips_match_the_plan_table():
    win, wdo = INSTRUMENTS["WIN"], INSTRUMENTS["WDO"]
    assert get_cost("WIN", "base").round_trip_brl(win) == pytest.approx(2.50)
    assert get_cost("WIN", "base").round_trip_points(win) == pytest.approx(12.5)
    assert get_cost("WIN", "conservative").round_trip_brl(win) == pytest.approx(5.00)
    assert get_cost("WIN", "stress").round_trip_brl(win) == pytest.approx(9.00)
    assert get_cost("WIN", "optimistic").round_trip_brl(win) == pytest.approx(0.50)
    assert get_cost("WDO", "base").round_trip_brl(wdo) == pytest.approx(12.0)
    assert get_cost("WDO", "conservative").round_trip_brl(wdo) == pytest.approx(23.0)
    rows = {(r["root"], r["scenario"]): r for r in cost_table()}
    assert rows[("WIN", "base")]["round_trip_pct_of_notional"] == pytest.approx(100 * 2.5 / 34_400)


def test_every_root_has_every_scenario_and_costs_increase():
    for root, scenarios in COSTS.items():
        assert set(scenarios) == set(REQUIRED_SCENARIOS)
        inst = INSTRUMENTS[root]
        rts = [scenarios[s].round_trip_brl(inst) for s in REQUIRED_SCENARIOS]
        assert rts == sorted(rts)
    with pytest.raises(ValueError):
        get_cost("WIN", "cheap")
