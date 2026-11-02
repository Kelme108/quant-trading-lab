import unittest

from lab.runner import _parse_recursive_stdout

TABLE = (
    "│     sma_fast │ nan% │ -0.000% │\n"
    "│     sma_slow │ nan% │ 0.000% │\n"
)
LOG = (
    "INFO - Using fee 0.1000% - worst case fee\n"
    "INFO - Price jump in BNB/USDT, 1h, spot between two candles of 23.53% detected.\n"
)


class ParseRecursiveTest(unittest.TestCase):
    def test_log_percentages_are_ignored(self) -> None:
        result = _parse_recursive_stdout(TABLE + LOG)
        self.assertTrue(result["recursive_is_stable"])
        self.assertEqual(result["recursive_nonzero_cells"], [])

    def test_nonzero_table_cell_is_unstable(self) -> None:
        result = _parse_recursive_stdout(TABLE + "│ rsi │ 0.120% │\n" + LOG)
        self.assertFalse(result["recursive_is_stable"])
        self.assertEqual(result["recursive_nonzero_cells"], ["0.120"])

    def test_no_variance_message_is_stable(self) -> None:
        self.assertTrue(_parse_recursive_stdout("No variance on indicator(s) found")["recursive_is_stable"])


if __name__ == "__main__":
    unittest.main()
