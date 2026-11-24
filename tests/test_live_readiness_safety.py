"""Guards for the path toward live trading.

1. No Freqtrade config visible to git carries an exchange key or secret: keys only
   come from the environment (FREQTRADE__EXCHANGE__KEY / __SECRET).
2. A config with dry_run=false must point at the Binance SPOT TESTNET (ccxt sandbox,
   sync and async). Real money needs a config that does not exist in this repo yet,
   and adding one must consciously change this test.
3. The testnet setup itself: spot, exchange-side stop, API off, keys via env_file,
   and its strategy kept outside the lab's strategy folder.
"""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
TESTNET_CONFIG = ROOT / "testnet" / "config.testnet.json"
TESTNET_COMPOSE = ROOT / "docker-compose.testnet.yml"


def _git_visible(pattern: str) -> list[Path]:
    """Tracked files plus new files git does not ignore."""
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", pattern],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [ROOT / line for line in out.splitlines() if line and (ROOT / line).is_file()]


def _freqtrade_configs() -> list[tuple[Path, dict]]:
    configs = []
    for path in _git_visible("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and ("dry_run" in data or isinstance(data.get("exchange"), dict)):
            configs.append((path, data))
    return configs


class LiveReadinessSafetyTests(unittest.TestCase):
    def test_configs_are_found(self) -> None:
        names = {p.relative_to(ROOT).as_posix() for p, _ in _freqtrade_configs()}
        self.assertIn("user_data/config.dryrun.json", names)
        self.assertIn("testnet/config.testnet.json", names)

    def test_no_config_holds_exchange_credentials(self) -> None:
        for path, config in _freqtrade_configs():
            exchange = config.get("exchange") or {}
            for field in ("key", "secret", "apiKey", "api_key", "password", "uid"):
                with self.subTest(config=path.relative_to(ROOT).as_posix(), field=field):
                    self.assertFalse(exchange.get(field), "credentials belong in the environment, not in a config file")

    def test_live_orders_only_reach_the_testnet(self) -> None:
        for path, config in _freqtrade_configs():
            if config.get("dry_run", True) is not False:
                continue
            exchange = config["exchange"]
            with self.subTest(config=path.relative_to(ROOT).as_posix()):
                self.assertEqual(exchange["name"], "binance")
                self.assertIs(exchange.get("ccxt_config", {}).get("sandbox"), True)
                self.assertIs(exchange.get("ccxt_async_config", {}).get("sandbox"), True)

    def test_no_env_file_is_visible_to_git(self) -> None:
        visible = [p.relative_to(ROOT).as_posix() for p in _git_visible("*.env") + _git_visible(".env")]
        self.assertEqual(visible, [])

    def test_testnet_config_shape(self) -> None:
        config = json.loads(TESTNET_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["trading_mode"], "spot")
        self.assertNotIn("margin_mode", config)
        self.assertTrue(config["order_types"]["stoploss_on_exchange"])
        self.assertFalse(config["force_entry_enable"])
        self.assertFalse(config["api_server"]["enabled"])
        self.assertFalse(config["telegram"]["enabled"])
        self.assertEqual(config["max_open_trades"], 1)
        self.assertIn("testnet", config["db_url"])

    def test_testnet_compose_reads_keys_from_env_file_only(self) -> None:
        compose = TESTNET_COMPOSE.read_text(encoding="utf-8")
        self.assertIn("freqtradeorg/freqtrade:2026.9", compose)
        self.assertIn("testnet/.env", compose)
        self.assertIn("/freqtrade/testnet/config.testnet.json", compose)
        self.assertNotIn("FREQTRADE__EXCHANGE__KEY=", compose)
        self.assertNotIn("ports:", compose)

    def test_mechanics_strategy_stays_out_of_the_lab(self) -> None:
        self.assertTrue((ROOT / "testnet" / "strategies" / "TestnetMechanics.py").is_file())
        self.assertEqual(list((ROOT / "user_data" / "strategies").rglob("TestnetMechanics*.py")), [])


if __name__ == "__main__":
    unittest.main()
