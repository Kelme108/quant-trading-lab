import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import tradereview  # noqa: E402


def trade(open_date, close_date, open_rate, close_rate, min_rate, max_rate, profit_ratio, profit_abs, reason,
          minutes, stake=10.0, fee=0.00175):
    return {
        "open_date": open_date, "close_date": close_date, "open_rate": open_rate, "close_rate": close_rate,
        "min_rate": min_rate, "max_rate": max_rate, "profit_ratio": profit_ratio, "profit_abs": profit_abs,
        "exit_reason": reason, "trade_duration": minutes, "stake_amount": stake, "fee_open": fee, "fee_close": fee,
    }


TRADES = [
    # winner: entered 100, best 130, closed 120 (net +0.18)
    trade("2020-01-01 00:00:00+00:00", "2020-01-20 00:00:00+00:00", 100.0, 120.0, 95.0, 130.0, 0.18, 1.8, "channel", 19 * 24 * 60),
    # stopped loser that had been +3% in profit before it lost
    trade("2020-02-01 00:00:00+00:00", "2020-02-02 00:00:00+00:00", 100.0, 94.0, 93.0, 103.0, -0.0633, -0.633, "stop_loss", 24 * 60),
    # quick re-entry (opens 2 h after the previous close), 1 h long, small loss
    trade("2020-02-02 02:00:00+00:00", "2020-02-02 03:00:00+00:00", 100.0, 99.0, 98.5, 100.2, -0.0117, -0.117, "channel", 60),
    # winner in a later year
    trade("2021-03-01 00:00:00+00:00", "2021-03-10 00:00:00+00:00", 100.0, 110.0, 99.0, 112.0, 0.0983, 0.983, "channel", 9 * 24 * 60),
]


class ExcursionTests(unittest.TestCase):
    def test_mae_and_mfe_come_from_the_exported_extremes(self) -> None:
        mae, mfe = tradereview.excursions(TRADES[0])
        self.assertAlmostEqual(mae, -0.05)
        self.assertAlmostEqual(mfe, 0.30)

    def test_missing_extremes_give_none(self) -> None:
        self.assertEqual(tradereview.excursions({"open_rate": 100.0}), (None, None))

    def test_mae_is_never_positive_and_mfe_never_negative(self) -> None:
        mae, mfe = tradereview.excursions(trade("a", "b", 100.0, 100.0, 101.0, 99.0, 0, 0, "x", 60))
        self.assertEqual(mae, 0.0)
        self.assertEqual(mfe, 0.0)

    def test_summary_separates_winners_and_losers_and_counts_green_losers(self) -> None:
        s = tradereview.excursion_summary(TRADES)
        self.assertTrue(s["available"])
        self.assertEqual((s["winners"], s["losers"]), (2, 2))
        self.assertEqual(s["losers_green_before_loss"], 1)  # the stopped trade had been +3%
        self.assertAlmostEqual(s["losers_green_before_loss_share"], 0.5)
        # winner 1: MFE 0.30, realised 0.18 -> give-back 0.12; winner 2: MFE 0.12, realised 0.0983 -> 0.0217
        self.assertAlmostEqual(s["winner_mean_giveback_pct"], (0.12 + 0.0217) / 2 * 100, places=3)

    def test_summary_without_extremes_is_marked_unavailable(self) -> None:
        bare = [{"open_rate": 100.0, "profit_ratio": 0.1, "profit_abs": 1.0}]
        self.assertEqual(tradereview.excursion_summary(bare), {"available": False})


class TableTests(unittest.TestCase):
    def test_exit_reason_rows_add_up_to_the_total(self) -> None:
        rows = tradereview.exit_reason_table(TRADES)
        self.assertEqual(sum(r["trades"] for r in rows), len(TRADES))
        self.assertAlmostEqual(sum(r["net_profit_abs"] for r in rows), sum(t["profit_abs"] for t in TRADES))
        self.assertEqual(rows[0]["exit_reason"], "channel")  # largest group first
        self.assertAlmostEqual(sum(r["share_of_net"] for r in rows), 1.0)

    def test_share_of_net_is_none_when_the_total_is_not_positive(self) -> None:
        losing = [trade("a", "b", 100, 90, 90, 100, -0.1, -1.0, "stop_loss", 60)]
        self.assertIsNone(tradereview.exit_reason_table(losing)[0]["share_of_net"])

    def test_duration_buckets_cover_every_trade_exactly_once(self) -> None:
        rows = tradereview.duration_table(TRADES)
        self.assertEqual(sum(r["trades"] for r in rows), len(TRADES))
        by = {r["bucket"]: r for r in rows}
        self.assertEqual(by["< 3 h"]["trades"], 1)
        self.assertEqual(by["3 h a 1 dia"]["trades"], 0)  # exactly 24 h falls in the next bucket
        self.assertEqual(by["1 a 7 dias"]["trades"], 1)
        self.assertEqual(by["7 a 30 dias"]["trades"], 2)

    def test_quick_reentries_and_short_trades(self) -> None:
        sq = tradereview.short_and_quick(TRADES)
        self.assertEqual(sq["short"]["trades"], 1)
        self.assertEqual(sq["quick_reentry"]["trades"], 1)
        self.assertAlmostEqual(sq["quick_reentry"]["net_profit_abs"], -0.117)

    def test_concentration(self) -> None:
        c = tradereview.concentration(TRADES)
        net = sum(t["profit_abs"] for t in TRADES)
        self.assertAlmostEqual(c["net_profit_abs"], net)
        self.assertAlmostEqual(c["top1_share"], 1.8 / net)
        self.assertAlmostEqual(c["profit_excl_best_abs"], net - 1.8)
        self.assertEqual(set(c["net_by_year"]), {"2020", "2021"})
        self.assertAlmostEqual(sum(c["net_by_year"].values()), net)


class CostTests(unittest.TestCase):
    def test_fees_follow_stake_and_both_legs(self) -> None:
        one = [trade("a", "b", 100, 110, 100, 110, 0.10, 1.0, "x", 60, stake=10.0, fee=0.001)]
        c = tradereview.cost_share(one)
        self.assertAlmostEqual(c["fees_paid_abs"], 10.0 * 0.001 + 10.0 * 1.10 * 0.001)
        self.assertAlmostEqual(c["gross_profit_abs"], 1.0 + c["fees_paid_abs"])

    def test_missing_fee_fields_give_none(self) -> None:
        c = tradereview.cost_share([{"profit_ratio": 0.1, "profit_abs": 1.0}])
        self.assertIsNone(c["fees_paid_abs"])


class ReviewTests(unittest.TestCase):
    def test_empty_list(self) -> None:
        self.assertEqual(tradereview.review([]), {"trades": 0})
        self.assertIn("Sem trades", tradereview.render_markdown("t", "src", {"BTC/USDT": {"trades": 0}}))

    def test_review_is_deterministic_and_renders(self) -> None:
        a, b = tradereview.review(TRADES), tradereview.review(list(TRADES))
        self.assertEqual(a, b)
        text = tradereview.render_markdown("Titulo", "arquivo.zip", {"BTC/USDT": a})
        for expected in ("Por motivo de saída", "Por duração", "Excursões", "arquivo.zip", "stop_loss"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
