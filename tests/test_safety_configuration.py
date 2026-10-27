import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SafetyConfigurationTests(unittest.TestCase):
    def test_tracked_config_is_safe_by_default(self) -> None:
        config = json.loads((ROOT / "user_data" / "config.dryrun.json").read_text())
        self.assertTrue(config["dry_run"])
        self.assertEqual(config["trading_mode"], "spot")
        self.assertEqual(config["exchange"]["key"], "")
        self.assertEqual(config["exchange"]["secret"], "")
        self.assertFalse(config["api_server"]["enabled"])
        self.assertEqual(config["api_server"]["listen_ip_address"], "127.0.0.1")
        self.assertEqual(config["api_server"]["jwt_secret_key"], "")
        self.assertEqual(config["api_server"]["username"], "")
        self.assertEqual(config["api_server"]["password"], "")
        self.assertNotIn("margin_mode", config)

    def test_compose_is_pinned_and_does_not_restart(self) -> None:
        compose = (ROOT / "docker-compose.yml").read_text()
        self.assertIn("freqtradeorg/freqtrade:2026.9", compose)
        self.assertNotIn("freqtradeorg/freqtrade:stable", compose)
        self.assertIn('restart: "no"', compose)
        self.assertIn('127.0.0.1:8080:8080', compose)


if __name__ == "__main__":
    unittest.main()
