"""lab/universes.py: a lane's reads become the same structures the crypto Resultados pages read. Synthetic lane."""

import json

import pytest

from lab import universes as U

COLS = ["entry_time", "exit_time", "side", "entry_price", "exit_price", "gross_pct", "net_pct", "entry_reason", "exit_reason"]


def _result(rule, symbol, split, decision, net):
    sc = {k: {"trades": 3, "trades_per_year": 100.0, "net_return_pct": net - i, "max_drawdown_pct": 1.5}
          for i, k in enumerate(("optimistic", "base", "conservative", "stress"))}
    return {"rule": rule, "strategy": f"{rule}_toy_rule", "symbol": symbol, "split": split, "scenarios": sc,
            "gates": {"decision": decision, "fails": [] if decision == "passed" else ["base: net <= bar"], "net_bar_pct": 1.0},
            "read_at_utc": "2026-11-16T12:00:00+00:00", "start_utc": "2022-01-01", "end_utc": "2024-01-01",
            "cost_round_trip_base_pct": 0.011, "prior_variants": 0}


@pytest.fixture
def lane(tmp_path, monkeypatch):
    d = tmp_path / "research" / "b3"
    (d / "results").mkdir(parents=True)
    (d / "trades").mkdir()
    rows = [["2022-03-01T13:00:00+00:00", "2022-03-01T14:00:00+00:00", "long", 110000.0, 110100.0, 0.09, 0.08, "x", "exit_signal"],
            ["2022-03-02T13:00:00+00:00", "2022-03-02T13:30:00+00:00", "short", 110000.0, 110050.0, -0.045, -0.055, "y", "stop_loss"],
            ["2022-03-03T13:00:00+00:00", "2022-03-03T15:00:00+00:00", "long", 110000.0, 110200.0, 0.18, 0.17, "x", "end_of_day_flatten"]]
    for rule, sym, split, dec in (("P-004", "WIN", "exploration", "passed"), ("P-004", "WIN", "validation", "rejected"),
                                  ("P-001", "WDO", "exploration", "rejected"), ("P-001", "WDO", "final_test", "rejected")):
        stem = f"{rule}-{sym}-{split}-2026-11-16T120000"
        (d / "results" / f"{stem}.json").write_text(json.dumps(_result(rule, sym, split, dec, 2.0)), encoding="utf-8")
        (d / "trades" / f"{stem}.json").write_text(json.dumps({"columns": COLS, "rows": rows}), encoding="utf-8")
    (d / "ledger.jsonl").write_text("\n".join(json.dumps({"rule": r, "symbol": s, "split": "exploration"})
                                              for r, s in (("P-004", "WIN"), ("P-001", "WDO"))) + "\n", encoding="utf-8")
    (tmp_path / "b3" / "config").mkdir(parents=True)
    (tmp_path / "b3" / "config" / "gates_b3.json").write_text(json.dumps({"minimum_trades": 30, "net_return_pct_floor": 1.0,
                                                                         "per_variant_increase": 0.1}), encoding="utf-8")
    return tmp_path


def test_a_lane_becomes_hypotheses_rows_index_and_experiments(lane):
    u = U.build_universe("b3", lane)
    ids = [h["id"] for h in u["hypotheses"]]
    assert ids == ["P-001", "P-004"]
    p4 = next(h for h in u["hypotheses"] if h["id"] == "P-004")
    assert p4["status"] == "not approved at validation"
    assert {c["split"] for c in p4["cells"]} == {"exploration", "validation"}
    assert all(not any(c["split"] == "final_test" for c in h["cells"]) for h in u["hypotheses"])   # locked split out
    rows = {(r["id"], r["stage"]): r for r in u["strategies"]}
    assert rows[("P-004", "exploration")]["trades"] == 3 and rows[("P-004", "exploration")]["gates_all_pass"] is True
    assert rows[("P-004", "exploration")]["roi_pct"] == pytest.approx(0.08 - 0.055 + 0.17, abs=1e-6)
    assert len(u["trade_index"]["trades"]) == 9 and u["pairs"] == ["WDO", "WIN"]
    assert u["gate_bar"]["trials"] == 2 and u["gate_bar"]["current_bar_pct"] == pytest.approx(1.2)
    assert all(e["id"].startswith("b3.") for e in u["experiments"]["items"])


def test_the_chart_payload_has_the_crypto_shape_and_refuses_the_final_test(lane, monkeypatch):
    monkeypatch.setattr(U, "_candles", lambda *a, **k: [[1, 1.0, 1.0, 1.0, 1.0, 1.0]])
    status, body = U.trades_payload("b3.P-004-WIN-exploration-2026-11-16T120000", lane)
    assert status == 200 and body["pair"] == "WIN" and len(body["trades"]) == 3
    t = body["trades"][0]
    assert {"open_ts", "close_ts", "open_rate", "close_rate", "profit_ratio", "exit_reason", "n"} <= set(t)
    assert U.trades_payload("b3.P-001-WDO-final_test-2026-11-16T120000", lane)[0] == 404
    assert U.trades_payload("b3.../../etc", lane)[0] == 404
    assert U.trades_payload("nope.P-004-WIN-exploration-2026-11-16T120000", lane)[0] == 404


def test_the_page_assets_route_every_universe():
    js = (U.ROOT / "lab" / "dashboard_assets" / "universes.js").read_text(encoding="utf-8")
    for uid in U.UNIVERSES:
        assert f"{uid}:" in js            # UX_META has an entry for every server universe
    from lab import dashboard
    assert set(dashboard.UNIVERSE_IDS) == set(U.UNIVERSES)
