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
