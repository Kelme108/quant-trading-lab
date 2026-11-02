import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lab import runner


class BacktestStakeTests(unittest.TestCase):
    """Regression: a fixed stake equal to the wallet stops all trading after
    the first loss (1 trade instead of 284 on the same ETH/USDT run)."""

    def run_backtest_capturing_args(self, **kwargs) -> list[str]:
        captured: list[str] = []

        def fake_run_compose(args, cwd=None):
            captured.extend(args)
            return subprocess.CompletedProcess(args, returncode=1, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(runner, "run_compose", fake_run_compose),
                mock.patch.object(runner, "USER_DATA", Path(tmp) / "user_data"),
                mock.patch.object(runner, "EXPERIMENTS_DIR", Path(tmp) / "experiments"),
            ):
                runner.run_backtest(
                    experiment_id="t", strategy="S", timerange="1-2", fee=0.001, **kwargs
                )
        return captured

    def value_of(self, args: list[str], flag: str) -> str:
        return args[args.index(flag) + 1]

    def test_stake_is_unlimited_by_default(self) -> None:
        args = self.run_backtest_capturing_args()
        self.assertEqual(self.value_of(args, "--stake-amount"), "unlimited")

    def test_an_explicit_stake_is_still_honored(self) -> None:
        args = self.run_backtest_capturing_args(stake_amount=50.0)
        self.assertEqual(self.value_of(args, "--stake-amount"), "50.0")

    def test_protections_are_enabled_so_a_declared_cooldown_is_traded(self) -> None:
        self.assertIn("--enable-protections", self.run_backtest_capturing_args())

    def test_full_exposure_adds_no_overlay_config(self) -> None:
        args = self.run_backtest_capturing_args()
        self.assertEqual(args.count("--config"), 1)

    def test_partial_exposure_adds_an_overlay_config_after_the_main_one(self) -> None:
        args = self.run_backtest_capturing_args(exposure=0.2)
        positions = [i for i, a in enumerate(args) if a == "--config"]
        self.assertEqual(len(positions), 2)
        self.assertTrue(args[positions[0] + 1].endswith("config.dryrun.json"))
        self.assertTrue(args[positions[1] + 1].endswith("exposure.json"))

    def test_exposure_outside_zero_one_is_rejected(self) -> None:
        for bad in (0.0, -0.1, 1.5):
            with self.assertRaises(ValueError):
                self.run_backtest_capturing_args(exposure=bad)

    def test_the_pair_is_passed_through(self) -> None:
        args = self.run_backtest_capturing_args(pair="ETH/USDT")
        self.assertEqual(self.value_of(args, "--pairs"), "ETH/USDT")


class ProfitExcludingBestTradeTests(unittest.TestCase):
    def trades(self, *ratios: float) -> list[dict]:
        return [{"profit_ratio": r} for r in ratios]

    def test_no_trades_and_a_single_trade_give_zero(self) -> None:
        self.assertEqual(runner.compounded_profit_excluding_best([], 100.0), 0.0)
        self.assertEqual(runner.compounded_profit_excluding_best(self.trades(0.5), 100.0), 0.0)

    def test_removes_the_best_trade_and_compounds_the_rest(self) -> None:
        # +50%, -10%, +20% on 100: dropping +50% leaves 100 * 0.9 * 1.2 = 108.
        result = runner.compounded_profit_excluding_best(self.trades(0.5, -0.1, 0.2), 100.0)
        self.assertAlmostEqual(result, 8.0)

    def test_partial_exposure_scales_each_trade_by_its_share_of_the_balance(self) -> None:
        # 20% of a 100 account per trade: +50% -> +10 (balance 110, share 100*0.2/100);
        # then -10% on 22 (20% of 110) -> -2.2 (107.8); then +20% on 21.56 -> +4.312.
        trades = [
            {"open_date": "2020-01-01", "profit_ratio": 0.5, "stake_amount": 20.0, "profit_abs": 10.0},
            {"open_date": "2020-02-01", "profit_ratio": -0.1, "stake_amount": 22.0, "profit_abs": -2.2},
            {"open_date": "2020-03-01", "profit_ratio": 0.2, "stake_amount": 21.56, "profit_abs": 4.312},
        ]
        # Without the +50% trade: 100 * (1 - 0.2*0.1) * (1 + 0.2*0.2)
        expected = 100 * (1 - 0.02) * (1 + 0.04) - 100
        self.assertAlmostEqual(runner.compounded_profit_excluding_best(trades, 100.0), expected)

    def test_order_of_trades_does_not_matter(self) -> None:
        forward = runner.compounded_profit_excluding_best(self.trades(0.5, -0.1, 0.2), 100.0)
        reverse = runner.compounded_profit_excluding_best(self.trades(0.2, -0.1, 0.5), 100.0)
        self.assertAlmostEqual(forward, reverse)

    def test_a_run_that_only_wins_through_one_trade_goes_negative(self) -> None:
        result = runner.compounded_profit_excluding_best(self.trades(2.0, -0.1, -0.1), 100.0)
        self.assertLess(result, 0.0)

    def test_the_best_trade_early_also_enlarges_later_trades(self) -> None:
        """+100% then +10% on 100 ends at 220 (profit 120). The best trade's own
        profit_abs is 100, so plain subtraction would say 20. Without it the
        second trade would have earned only 10% of 100, so the answer is 10."""
        result = runner.compounded_profit_excluding_best(self.trades(1.0, 0.1), 100.0)
        self.assertAlmostEqual(result, 10.0)
        self.assertNotAlmostEqual(result, 120.0 - 100.0)


if __name__ == "__main__":
    unittest.main()
