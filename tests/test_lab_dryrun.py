import unittest

from lab import dryrun

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


if __name__ == "__main__":
    unittest.main()
