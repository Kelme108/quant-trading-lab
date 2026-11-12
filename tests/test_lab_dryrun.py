import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parent))

from lab import dryrun, forward  # noqa: E402
from test_lab_forward import CLOSED, OPEN, make_database  # noqa: E402

CFG = dryrun.load_config()


def trade(i, ratio, stake=100.0):
    return {"open_date": f"2026-11-{1 + i // 4:02d} 00:00:00", "close_date": f"2026-11-{1 + i // 4:02d} 0{i % 4 + 1}:00:00",
            "profit_ratio": ratio, "profit_abs": ratio * stake}


def book(n, win=0.012, loss=-0.006, every=2):
    """n trades, one winner out of every `every`."""
    return [trade(i, win if i % every == 0 else loss) for i in range(n)]


class DryRunVerdictTests(unittest.TestCase):
    def judge(self, trades, wallet=1000.0, execution=None):
        m = dryrun.metrics(trades, wallet, CFG)
        return m, dryrun.verdict(m, CFG, execution)

    def test_few_trades_keep_collecting(self) -> None:
        m, (state, reasons) = self.judge(book(20))
        self.assertEqual(state, "collecting")
        self.assertIn("20/60", reasons[0])

    def test_a_good_book_is_approved_for_review_only_at_the_trade_count(self) -> None:
        m, (state, reasons) = self.judge(book(80))
        self.assertEqual(m["trades"], 80)
        self.assertAlmostEqual(m["profit_factor"], 2.0, places=6)
        self.assertAlmostEqual(m["payoff"], 2.0, places=6)
        self.assertEqual(state, "approved_for_review")
        self.assertTrue(all(r.startswith("pass") for r in reasons))

    def test_a_high_win_rate_with_a_small_payoff_loses_and_is_rejected(self) -> None:
        trades = [trade(i, 0.002 if i % 4 else -0.012) for i in range(80)]   # 75% winners, payoff 0.17
        m, (state, _) = self.judge(trades)
        self.assertGreater(m["win_rate"], 0.7)
        self.assertLess(m["profit_factor"], 1.0)
        self.assertEqual(state, "rejected")

    def test_a_clearly_losing_bot_is_rejected_early(self) -> None:
        m, (state, reasons) = self.judge(book(35, win=0.004, loss=-0.012, every=3))
        self.assertEqual(state, "rejected")
        self.assertIn("early reject", reasons[0])

    def test_profit_that_depends_on_one_trade_is_not_approved(self) -> None:
        trades = [trade(i, -0.001) for i in range(79)] + [trade(79, 0.2)]
        m, (state, reasons) = self.judge(trades)
        self.assertNotEqual(state, "approved_for_review")

    def test_expensive_real_fills_block_the_approval(self) -> None:
        m, (state, reasons) = self.judge(book(80), execution={"observed_entry_cost_per_side_mean": 0.01})
        self.assertEqual(state, "collecting")
        self.assertTrue(any(r.startswith("FAIL: observed entry cost") for r in reasons))

    def test_drawdown_and_bootstrap_are_deterministic(self) -> None:
        self.assertAlmostEqual(dryrun.max_drawdown_pct([10, -30, 5, -5, 40], 100.0), 30.0)
        a = dryrun.bootstrap_prob_positive([0.01, -0.005, 0.02, -0.01], 500, 1)
        self.assertEqual(a, dryrun.bootstrap_prob_positive([0.01, -0.005, 0.02, -0.01], 500, 1))
        self.assertEqual(dryrun.bootstrap_prob_positive([], 10, 1), 0.0)


CFG7 = {**CFG, "inactivity": {"warn_after_days": 3, "discard_after_days": 7, "min_trades_by_then": 5, "max_days_without_trade": 5,
                               "slow_eta_days": 30, "auto_retire": True}}


class InactivityTests(unittest.TestCase):
    """The inactivity logic, with explicit numbers (7 days, 5 trades, 5 quiet days) so it does not move with the owner's rule."""
    START = datetime(2026, 11, 1)

    def judge(self, trades, days_running, cfg=CFG7):
        now = self.START + timedelta(days=days_running)
        m = {**dryrun.metrics(trades, 1000.0, cfg), **dryrun.activity(trades, self.START, now, cfg)}
        return m, dryrun.verdict(m, cfg)

    def test_the_clock_starts_at_the_freeze_not_at_the_first_trade(self) -> None:
        m, (state, reasons) = self.judge([], 4.0)
        self.assertAlmostEqual(m["days_running"], 4.0)
        self.assertEqual(m["days"], 0.0)                     # the span of trades is still 0
        self.assertEqual((m["trades_per_day"], m["days_since_last_trade"], m["eta_days_to_min_trades"]), (0.0, None, None))
        self.assertEqual(state, "collecting")
        self.assertTrue(any(r.startswith("warning: no closed trade yet") for r in reasons))

    def test_no_trade_for_the_discard_age_is_discarded(self) -> None:
        for trades in ([], book(4)):
            _, (state, reasons) = self.judge(trades, 7.0)
            self.assertEqual(state, "inactive", reasons)
            self.assertTrue(any(r.startswith("INACTIVE") for r in reasons))

    def test_a_bot_that_trades_is_kept_and_its_pace_is_shown(self) -> None:
        m, (state, reasons) = self.judge(book(12), 7.0)     # 12 trades in 7 days
        self.assertEqual(state, "collecting")
        self.assertAlmostEqual(m["trades_per_day"], 12 / 7.0)
        self.assertAlmostEqual(m["eta_days_to_min_trades"], 48 / (12 / 7.0))
        self.assertFalse(any("INACTIVE" in r for r in reasons))

    def test_a_bot_that_went_quiet_is_discarded_after_the_discard_age(self) -> None:
        trades = [trade(i, 0.01) for i in range(8)]         # all trades on 2026-11-01 and 11-02
        _, (state, reasons) = self.judge(trades, 9.0)
        self.assertEqual(state, "inactive")
        self.assertTrue(any("no closed trade for" in r for r in reasons))
        _, (young, _) = self.judge(trades, 6.0)             # same silence, but still below the discard age
        self.assertEqual(young, "collecting")

    def test_inactivity_never_overrides_a_real_verdict(self) -> None:
        _, (state, _) = self.judge(book(35, win=0.004, loss=-0.012, every=3), 30.0)
        self.assertEqual(state, "rejected")

    def test_an_unknown_freeze_time_changes_nothing(self) -> None:
        m = {**dryrun.metrics([], 1000.0, CFG7), **dryrun.activity([], None, self.START, CFG7)}
        self.assertEqual(dryrun.verdict(m, CFG7)[0], "collecting")

    def test_the_report_lists_the_running_time_and_the_recommendation(self) -> None:
        m, (state, reasons) = self.judge([], 8.0)
        text = dryrun.render([{"hypothesis": "H-200", "verdict": state, "reasons": reasons, "pooled": m, "per_pair": {}, "wallet": 1000.0}], CFG7)
        self.assertIn("Rodando (dias)", text)
        self.assertIn("| H-200 | inactive | 8.0 | 0 | 0.00 |", text)
        self.assertIn("parar e descartar este bot", text)


class OwnerTwoDayRuleTests(unittest.TestCase):
    """Owner decision 2026-11-12, as shipped in lab/config/dryrun.json: a bot that does not trade for 2 days leaves the dry-run."""
    START = datetime(2026, 11, 1)

    def state(self, trades, days_running):
        now = self.START + timedelta(days=days_running)
        m = {**dryrun.metrics(trades, 1000.0, CFG), **dryrun.activity(trades, self.START, now, CFG)}
        return dryrun.verdict(m, CFG)[0]

    def test_the_shipped_rule_is_two_days_and_automatic(self) -> None:
        rule = CFG["inactivity"]
        self.assertEqual((rule["discard_after_days"], rule["min_trades_by_then"], rule["max_days_without_trade"]), (2, 1, 2))
        self.assertTrue(rule["auto_retire"])

    def test_no_trade_in_the_first_two_days_is_out(self) -> None:
        self.assertEqual(self.state([], 1.9), "collecting")
        self.assertEqual(self.state([], 2.0), "inactive")

    def test_a_bot_that_trades_every_day_stays_and_two_quiet_days_later_is_out(self) -> None:
        daily = [{"open_date": f"2026-11-{d:02d} 10:00:00", "close_date": f"2026-11-{d:02d} 12:00:00", "profit_ratio": 0.004, "profit_abs": 1.0}
                 for d in range(1, 6)]                                       # one trade a day, 1st to 5th
        self.assertEqual(self.state(daily, 5.0), "collecting")              # last close 4.5 days after the start
        self.assertEqual(self.state(daily, 6.4), "collecting")              # quiet for 1.9 days
        self.assertEqual(self.state(daily, 6.6), "inactive")                # quiet for 2.1 days


class RetireTests(unittest.TestCase):
    """An inactive bot is stopped and its freeze moves to research/forward/retired/; nothing is deleted."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        folder = self.root / "research" / "forward"
        folder.mkdir(parents=True)
        (folder / "H-200-freeze.json").write_text(json.dumps({"hypothesis": "H-200", "frozen_at_utc": "2026-11-01T00:00:00+00:00",
                                                              "strategy": {"class": "X_H200_v1"}, "databases": {"BTC/USDT": "x"}}), encoding="utf-8")
        self.stopped = []

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_retire_stops_the_bot_and_moves_the_freeze(self) -> None:
        done = dryrun.retire("H-200", ["INACTIVE: 0 closed trades in 2.0 days"], self.root,
                             stop=lambda compose, root: (self.stopped.append(compose) or (True, "")), now=datetime(2026, 11, 3))
        self.assertTrue(done["retired"])
        self.assertEqual(self.stopped, ["docker-compose.forward.h200.yml"])
        self.assertFalse((self.root / "research/forward/H-200-freeze.json").exists())
        moved = json.loads((self.root / "research/forward/retired/H-200-freeze.json").read_text(encoding="utf-8"))
        self.assertEqual(moved["retired"]["verdict"], "inactive")
        self.assertEqual(dryrun.frozen_hypotheses(self.root), [])           # no longer judged nor counted
        self.assertEqual(dryrun.retired_records(self.root)[0]["hypothesis"], "H-200")

    def test_a_failed_stop_keeps_the_bot_visible(self) -> None:
        done = dryrun.retire("H-200", [], self.root, stop=lambda compose, root: (False, "docker down"))
        self.assertFalse(done["retired"])
        self.assertEqual(dryrun.frozen_hypotheses(self.root), ["H-200"])

    def test_the_report_lists_the_retired_bots(self) -> None:
        dryrun.retire("H-200", ["INACTIVE: 0 closed trades in 2.0 days"], self.root, stop=lambda c, r: (True, ""), now=datetime(2026, 11, 3))
        text = dryrun.render([], CFG, dryrun.retired_records(self.root))
        self.assertIn("## Retirados do dry-run", text)
        self.assertIn("| H-200 | X_H200_v1 | 2026-11-01T00:00 | 2026-11-03T00:00 | INACTIVE: 0 closed trades in 2.0 days |", text)


def multi_pair_root(root: Path, pairs: list[str], wallet_per_pair: float = 1000.0) -> None:
    overlay = {"bot_name": "forward-h105", "strategy": "X_H105_v1", "db_url": f"sqlite:///{forward.multi_database_path('H-105')}",
               "max_open_trades": len(pairs), "stake_amount": "unlimited", "tradable_balance_ratio": 0.25,
               "dry_run_wallet": wallet_per_pair * len(pairs), "exchange": {"pair_whitelist": pairs}}
    path = root / forward.multi_overlay_path("H-105")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overlay), encoding="utf-8")
    (root / "user_data").mkdir(exist_ok=True)


class MultiPairBotTests(unittest.TestCase):
    """One bot for several pairs is judged exactly like several one-pair bots with 1000 USDT each."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        multi_pair_root(self.root, ["ETH/USDT", "SOL/USDT", "BTC/USDT"])
        eth_loss = {**CLOSED, "id": 1, "pair": "ETH/USDT", "close_profit": -0.2, "close_profit_abs": -50.0,
                    "close_date": "2026-11-02 10:00:00.000000"}
        eth_win = {**CLOSED, "id": 2, "pair": "ETH/USDT", "close_profit": 0.1, "close_profit_abs": 25.0}
        sol = {**CLOSED, "id": 3, "pair": "SOL/USDT", "close_profit": 0.04, "close_profit_abs": 10.0}
        sol_open = {**OPEN, "id": 4, "pair": "SOL/USDT"}
        make_database(self.root / forward.multi_database_path("H-105"), [eth_loss, eth_win, sol, sol_open], [])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_the_wallet_is_the_per_pair_equivalent_and_the_trades_are_split_by_pair(self) -> None:
        result = dryrun.evaluate_hypothesis("H-105", CFG, self.root)
        self.assertEqual(result["wallet"], 3000.0)                      # 3 pairs x 1000, as three one-pair bots
        self.assertEqual(set(result["per_pair"]), {"BTC/USDT", "ETH/USDT", "SOL/USDT"})
        self.assertEqual(result["per_pair"]["ETH/USDT"]["trades"], 2)
        self.assertEqual(result["per_pair"]["SOL/USDT"]["trades"], 1)   # the open trade is not counted
        self.assertEqual(result["per_pair"]["BTC/USDT"]["trades"], 0)
        self.assertAlmostEqual(result["per_pair"]["ETH/USDT"]["max_drawdown_pct"], 5.0)   # 50 of 1000, not of 3000
        self.assertEqual(result["pooled"]["trades"], 3)
        self.assertAlmostEqual(result["pooled"]["net_profit"], -15.0)
        self.assertAlmostEqual(result["pooled"]["max_drawdown_pct"], 100 * 50 / 3000)
        self.assertEqual(result["verdict"], "collecting")

    def test_same_trades_same_numbers_in_either_layout(self) -> None:
        per_pair = Path(self.tmp.name) / "per_pair"
        for key, pair in (("eth", "ETH/USDT"), ("sol", "SOL/USDT"), ("btc", "BTC/USDT")):
            path = per_pair / forward.overlay_path("H-105", key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"dry_run_wallet": 1000.0, "exchange": {"pair_whitelist": [pair]}}), encoding="utf-8")
            (per_pair / "user_data").mkdir(exist_ok=True)
            trades, _ = forward.read_pair("H-105", key, self.root)
            make_database(per_pair / forward.database_path("H-105", key), trades, [])
        a = dryrun.evaluate_hypothesis("H-105", CFG, self.root)
        b = dryrun.evaluate_hypothesis("H-105", CFG, per_pair)
        self.assertEqual((a["wallet"], a["per_pair"], a["pooled"]), (b["wallet"], b["per_pair"], b["pooled"]))


if __name__ == "__main__":
    unittest.main()
