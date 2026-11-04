import math
import unittest

from lab import analytics


def trade(day, ratio, stake=10.0, duration=60):
    return {"open_date": f"2024-01-{day:02d}T00:00:00+00:00", "close_date": f"2024-01-{day:02d}T12:00:00+00:00",
            "profit_ratio": ratio, "profit_abs": ratio * stake, "stake_amount": stake, "fee_open": 0.001, "fee_close": 0.001,
            "trade_duration": duration, "exit_reason": "roi" if ratio > 0 else "stop_loss"}


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.trades = [trade(1, 0.10), trade(2, -0.05), trade(3, 0.05), trade(4, -0.02), trade(5, 0.04), trade(6, 0.04)]
        self.m = analytics.trade_metrics(self.trades, 100.0)

    def test_basic_counts_and_rates(self):
        self.assertEqual((self.m["trades"], self.m["wins"], self.m["losses"]), (6, 4, 2))
        self.assertAlmostEqual(self.m["winrate"], 4 / 6)

    def test_profit_factor_expectancy_roi(self):
        gross_win, gross_loss = (0.10 + 0.05 + 0.04 + 0.04) * 10, (0.05 + 0.02) * 10
        self.assertAlmostEqual(self.m["profit_factor"], gross_win / gross_loss)
        net = gross_win - gross_loss
        self.assertAlmostEqual(self.m["net_profit_abs"], net)
        self.assertAlmostEqual(self.m["roi_pct"], net)            # wallet 100
        self.assertAlmostEqual(self.m["expectancy_abs"], net / 6)
        self.assertAlmostEqual(self.m["expectancy_pct"], (0.10 - 0.05 + 0.05 - 0.02 + 0.04 + 0.04) / 6 * 100)

    def test_payoff_best_trade_and_concentration(self):
        self.assertAlmostEqual(self.m["avg_win_pct"], 5.75)
        self.assertAlmostEqual(self.m["avg_loss_pct"], -3.5)
        self.assertAlmostEqual(self.m["payoff"], 5.75 / 3.5)
        self.assertAlmostEqual(self.m["profit_excl_best_abs"], self.m["net_profit_abs"] - 1.0)
        self.assertAlmostEqual(self.m["top_trade_share"], 1.0 / self.m["net_profit_abs"])

    def test_no_losers_gives_none_not_infinity(self):
        m = analytics.trade_metrics([trade(1, 0.01), trade(2, 0.02)], 100.0)
        self.assertIsNone(m["profit_factor"])
        self.assertEqual(m["profit_factor_note"], "sem trades perdedores")

    def test_empty_trade_list(self):
        m = analytics.trade_metrics([], 100.0)
        self.assertEqual(m["trades"], 0)
        self.assertIsNone(m["winrate"])

    def test_wilson_interval_brackets_the_rate_and_narrows_with_n(self):
        lo, hi = analytics.wilson_interval(6, 10)
        self.assertLess(lo, 0.6)
        self.assertGreater(hi, 0.6)
        lo2, hi2 = analytics.wilson_interval(600, 1000)
        self.assertLess(hi2 - lo2, hi - lo)
        self.assertIsNone(analytics.wilson_interval(0, 0))

    def test_streaks(self):
        self.assertEqual(analytics.streaks([1, 1, -1, -1, -1, 1]), {"max_win": 2, "max_loss": 3, "current": 1})
        self.assertEqual(analytics.streaks([]), {"max_win": 0, "max_loss": 0, "current": 0})
        self.assertEqual(analytics.streaks([-1, -1])["current"], -2)

    def test_histogram_counts_every_trade_and_is_centred_on_zero(self):
        h = analytics.histogram([-4.0, -1.0, 0.0, 1.0, 2.0, 4.0])
        self.assertEqual(sum(h["counts"]), 6)
        self.assertEqual(len(h["edges"]), len(h["counts"]) + 1)
        self.assertAlmostEqual(h["edges"][len(h["counts"]) // 2] + h["edges"][len(h["counts"]) // 2 + 1], 0.0)

    def test_monthly_sums_to_net_roi(self):
        total = sum(v for _, v in self.m["monthly"])
        self.assertAlmostEqual(total, self.m["roi_pct"])

    def test_fees_are_estimated_from_the_export_fields(self):
        t = trade(1, 0.0, stake=10.0)
        self.assertAlmostEqual(analytics.trade_metrics([t], 100.0)["fees_paid_abs"], 10 * 0.001 + 10 * 0.001)

    def test_cumulative_profit_and_downsample(self):
        pts = analytics.cumulative_profit(self.trades)
        self.assertAlmostEqual(pts[-1][1], self.m["net_profit_abs"])
        many = [[i, i] for i in range(1000)]
        small = analytics.downsample(many, 100)
        self.assertEqual((len(small), small[0], small[-1]), (100, [0, 0], [999, 999]))


class ScoreAndFlagTests(unittest.TestCase):
    def strong(self, **kw):
        row = {"profit_factor": 2.5, "roi_pct": 120.0, "roi_stress_pct": 90.0, "max_dd_pct": 12.0, "min_trades_pair": 60,
               "trades": 200, "n_pairs": 3, "pairs_positive": 3, "pairs_excl_best_positive": 3, "positive_year_share": 0.8,
               "stage": "exploration", "gates_all_pass": True}
        row.update(kw)
        return row

    def test_strong_strategy_scores_high_and_weak_scores_low(self):
        strong, _ = analytics.evidence_score(self.strong())
        weak, _ = analytics.evidence_score(self.strong(roi_pct=-5.0, profit_factor=0.8, max_dd_pct=45.0, pairs_positive=0,
                                                         pairs_excl_best_positive=0, positive_year_share=0.1))
        self.assertGreater(strong, 70)
        self.assertLess(weak, 25)

    def test_small_sample_caps_the_score(self):
        score, parts = analytics.evidence_score(self.strong(min_trades_pair=8))
        self.assertLessEqual(score, 40.0)
        self.assertTrue(parts["capped_by_sample"])

    def test_win_rate_does_not_enter_the_score(self):
        a = analytics.evidence_score(self.strong(winrate=0.2))[0]
        b = analytics.evidence_score(self.strong(winrate=0.9))[0]
        self.assertEqual(a, b)

    def test_weights_sum_to_100(self):
        self.assertEqual(sum(analytics.SCORE_WEIGHTS.values()), 100)

    def test_flags_report_numbers_and_levels(self):
        f = analytics.flags(self.strong(min_trades_pair=8, max_dd_pct=31.0, pairs_excl_best_positive=1, roi_stress_pct=-2.0, pairs_positive=2))
        keys = {x["key"]: x for x in f}
        for k in ("sample", "drawdown", "one_trade", "costs", "pairs"):
            self.assertIn(k, keys)
        self.assertIn("8 trades", keys["sample"]["text"])
        self.assertIn("31.0%", keys["drawdown"]["text"])
        self.assertEqual(keys["drawdown"]["level"], "bad")

    def test_overfit_flag_needs_the_other_stage(self):
        row = self.strong()
        self.assertNotIn("overfit", {x["key"] for x in analytics.flags(row)})
        f = analytics.flags(row, other_stage={"roi_pct": -1.0, "profit_factor": 0.9})
        self.assertIn("overfit", {x["key"] for x in f})
        self.assertNotIn("overfit", {x["key"] for x in analytics.flags(row, other_stage={"roi_pct": 80.0, "profit_factor": 2.2})})

    def test_worsening_flag(self):
        f = analytics.flags(self.strong(expectancy_first_pct=1.0, expectancy_last_pct=0.1, trades_last=40))
        self.assertIn("worsening", {x["key"] for x in f})
        f = analytics.flags(self.strong(expectancy_first_pct=1.0, expectancy_last_pct=0.9, trades_last=40))
        self.assertNotIn("worsening", {x["key"] for x in f})
        f = analytics.flags(self.strong(expectancy_first_pct=1.0, expectancy_last_pct=0.1, trades_last=8))
        self.assertNotIn("worsening", {x["key"] for x in f})          # too few trades in the last third to say

    def test_gate_rejection_caps_the_score_but_a_pass_does_not(self):
        free = analytics.evidence_score(self.strong())[0]
        rejected = analytics.evidence_score(self.strong(gates_any_rejected=True))
        self.assertGreater(free, analytics.GATE_REJECT_CAP)
        self.assertEqual(rejected[0], analytics.GATE_REJECT_CAP)
        self.assertTrue(rejected[1]["capped_by_gates"])

    def test_good_strategy_has_no_bad_flags(self):
        f = analytics.flags(self.strong(roi_stress_pct=90.0))
        self.assertFalse([x for x in f if x["level"] == "bad"])


if __name__ == "__main__":
    unittest.main()
