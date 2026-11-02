import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXAMPLE = ROOT / "docs" / "config.production.example.json"


class ProductionExampleConfigTests(unittest.TestCase):
    """The example is a starting point only. It must stay inert until the user
    deliberately copies it, fills secrets from the environment and flips dry_run."""

    def setUp(self) -> None:
        self.config = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_is_inert(self) -> None:
        self.assertTrue(self.config["dry_run"])
        self.assertEqual(self.config["initial_state"], "stopped")
        self.assertEqual(self.config["exchange"]["key"], "")
        self.assertEqual(self.config["exchange"]["secret"], "")
        self.assertEqual(self.config["telegram"]["token"], "")
        self.assertFalse(self.config["api_server"]["enabled"])

    def test_example_is_spot_only_with_exchange_side_stop(self) -> None:
        self.assertEqual(self.config["trading_mode"], "spot")
        self.assertNotIn("margin_mode", self.config)
        self.assertTrue(self.config["order_types"]["stoploss_on_exchange"])
        self.assertFalse(self.config["force_entry_enable"])
        self.assertLess(self.config["tradable_balance_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
