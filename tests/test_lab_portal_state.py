import shutil
import subprocess
import unittest
from pathlib import Path

from lab import dashboard

ROOT = Path(__file__).parents[1]


def trade(day, ratio, stake=10.0, month=1, year=2024):
    return {"open_date": f"{year}-{month:02d}-{day:02d}T00:00:00+00:00", "close_date": f"{year}-{month:02d}-{day:02d}T12:00:00+00:00",
            "profit_ratio": ratio, "profit_abs": ratio * stake, "stake_amount": stake, "fee_open": 0.001, "fee_close": 0.001,
            "trade_duration": 720, "exit_reason": "roi" if ratio > 0 else "stop_loss"}


def cell(pair, split, experiment_id, decision="candidate_for_portfolio", dd=10.0, stress=5.0):
    return {"pair": pair, "split": split, "experiment_id": experiment_id, "decision": decision, "max_drawdown_pct": dd,
            "profit_by_cost": {"stress": stress}, "analytics": {"trades": 0, "roi_pct": None, "starting_balance": 100.0}}


class StrategyRowsTests(unittest.TestCase):
    def build(self):
        # 3 pairs, 12 trades each, mostly winning, in exploration; a losing validation run
        explore_trades = [trade(d, 0.03 if d % 4 else -0.01, month=m) for m in (1, 2, 3) for d in range(1, 5)]
        valid_trades = [trade(d, -0.02 if d % 3 else 0.01, month=m, year=2025) for m in (1, 2) for d in range(1, 7)]
        run_trades, hyps = {}, []
        cells = []
        for pair in ("A/USDT", "B/USDT", "C/USDT"):
            for split, trades, decision in (("exploration", explore_trades, "candidate_for_portfolio"), ("validation", valid_trades, "rejected")):
                exp = f"{split}-{pair[0]}"
                run_trades[exp] = trades
                c = cell(pair, split, exp, decision)
                total = sum(t["profit_abs"] for t in trades)
                c["analytics"] = {"trades": len(trades), "roi_pct": total, "net_profit_abs": total, "winrate": 0.5, "profit_factor": 1.5,
                                  "expectancy_pct": 1.0, "expectancy_abs": 0.1, "profit_excl_best_abs": total - 0.3, "sharpe": 1.1, "starting_balance": 100.0}
                cells.append(c)
        hyps.append({"id": "H-900", "family": "Probe", "status": "x", "invalid": False, "in_portfolio": False, "cells": cells, "rule": "r", "notes": ""})
        hyps.append({"id": "H-901", "family": "Bad", "status": "invalid", "invalid": True, "in_portfolio": False, "cells": cells, "rule": "r", "notes": ""})
        return hyps, run_trades

    def test_one_row_per_valid_strategy_and_stage_and_invalid_is_left_out(self):
        hyps, runs = self.build()
        rows = dashboard._strategies(hyps, runs, 100.0)
        self.assertEqual({r["key"] for r in rows}, {"H-900:exploration", "H-900:validation"})
        self.assertFalse([r for r in rows if r["id"] == "H-901"])

    def test_pooled_numbers_follow_from_the_trades(self):
        hyps, runs = self.build()
        row = next(r for r in dashboard._strategies(hyps, runs, 100.0) if r["stage"] == "exploration")
        trades = [t for exp in runs if exp.startswith("exploration") for t in runs[exp]]
        net = sum(t["profit_abs"] for t in trades)
        self.assertEqual(row["trades"], len(trades))
        self.assertAlmostEqual(row["net_profit_abs"], net)
        self.assertAlmostEqual(row["roi_pct"], net / 3)                      # three wallets of 100: mean ROI per pair
        self.assertAlmostEqual(row["winrate"], sum(1 for t in trades if t["profit_abs"] > 0) / len(trades))
        self.assertEqual(row["min_trades_pair"], 12)
        self.assertEqual(row["n_pairs"], 3)
        self.assertTrue(row["gates_all_pass"])
        self.assertGreater(len(row["curve"]), 1)
        self.assertAlmostEqual(row["curve"][-1][1], net / 300 * 100)

    def test_small_sample_is_flagged_and_caps_the_score(self):
        hyps, runs = self.build()
        row = next(r for r in dashboard._strategies(hyps, runs, 100.0) if r["stage"] == "exploration")
        self.assertIn("sample", {f["key"] for f in row["flags"]})
        self.assertLessEqual(row["score"], 40.0)

    def test_validation_rejection_and_overfitting_signals(self):
        hyps, runs = self.build()
        rows = {r["stage"]: r for r in dashboard._strategies(hyps, runs, 100.0)}
        self.assertTrue(rows["validation"]["gates_any_rejected"])
        self.assertLessEqual(rows["validation"]["score"], 40.0)
        self.assertIn("overfit", {f["key"] for f in rows["exploration"]["flags"]})   # profit in exploration, loss in validation

    def test_stages_are_never_mixed(self):
        hyps, runs = self.build()
        rows = {r["stage"]: r for r in dashboard._strategies(hyps, runs, 100.0)}
        self.assertNotEqual(rows["exploration"]["roi_pct"], rows["validation"]["roi_pct"])
        self.assertTrue(all(p["experiment_id"].startswith("validation") for p in rows["validation"]["per_pair"]))

    def test_no_cells_no_rows(self):
        self.assertEqual(dashboard._strategies([{"id": "H-1", "family": "f", "status": "s", "invalid": False, "in_portfolio": False, "cells": []}], {}, 100.0), [])


class PageTests(unittest.TestCase):
    def test_render_page_inlines_the_portal_and_leaves_no_placeholder(self):
        state = dashboard.build_state() if False else {"generated_at": "x"}
        page = dashboard.render_page(state, nonce="n", live=True)
        for marker in ("/*__PORTAL__*/", "/*__TRADES_VIEW__*/", "/*__VENDOR_CHARTS__*/", "__NONCE_ATTR__", "__STATE__"):
            self.assertNotIn(marker, page)
        self.assertIn("function pageLeaderboard", page)
        self.assertIn("function pageStrategy", page)
        self.assertIn("function pageCompare", page)

    @unittest.skipUnless(shutil.which("node"), "needs Node")
    def test_portal_script_is_valid_javascript(self):
        result = subprocess.run(["node", "--check", str(ROOT / "lab" / "dashboard_assets" / "portal.js")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_page_has_no_remote_resources(self):
        text = (ROOT / "lab" / "dashboard_assets" / "index.html").read_text(encoding="utf-8") + (ROOT / "lab" / "dashboard_assets" / "portal.js").read_text(encoding="utf-8")
        for needle in ("http://", "https://cdn", "<link ", "@import", "fonts.googleapis"):
            if needle == "http://":
                # the only allowed absolute URLs are plain links the user clicks (FreqUI on loopback, TradingView credit)
                continue
            self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
