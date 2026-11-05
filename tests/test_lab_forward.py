import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from lab import forward, registry, tradereview  # noqa: E402

PAIR_NAMES = {"btc": "BTC/USDT", "eth": "ETH/USDT", "bnb": "BNB/USDT"}


def git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


class FreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(["init", "-q"], self.root)
        git(["config", "user.email", "t@example.com"], self.root)
        git(["config", "user.name", "T"], self.root)
        files = {
            "user_data/strategies/Thing_H009_v1.py": "# strategy\n",
            "docker-compose.forward.yml": "services:\n  a:\n    image: freqtradeorg/freqtrade:2026.9\n",
            "docker-compose.yml": "base compose\n",
            "user_data/config.dryrun.json": "{}\n",
        }
        for key in PAIR_NAMES:
            files[forward.overlay_path("H-009", key)] = json.dumps({"tradable_balance_ratio": 0.25})
        for name, text in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        git(["add", "-A"], self.root)
        git(["commit", "-q", "-m", "initial"], self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def freeze(self) -> dict:
        frozen = forward.build_freeze("H-009", self.root, now="2026-11-04T00:00:00+00:00")
        path = forward.freeze_path("H-009", self.root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(frozen), encoding="utf-8")
        return frozen

    def test_a_hypothesis_on_one_pair_with_its_own_compose_freezes_only_that_pair(self) -> None:
        extra = {
            "user_data/strategies/Mom_H016_v1.py": "# strategy\n",
            "docker-compose.forward.h016.yml": "services:\n  b:\n    image: freqtradeorg/freqtrade:2026.9\n",
            forward.overlay_path("H-016", "eth"): json.dumps({"tradable_balance_ratio": 0.15}),
        }
        for name, text in extra.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding="utf-8")
        git(["add", "-A"], self.root)
        git(["commit", "-q", "-m", "h016"], self.root)
        frozen = forward.build_freeze("H-016", self.root, now="2026-11-05T00:00:00+00:00")
        self.assertEqual(frozen["exposure_by_pair"], {"ETH/USDT": 0.15})
        self.assertEqual(set(frozen["databases"]), {"ETH/USDT"})
        self.assertIn("docker-compose.forward.h016.yml", frozen["files"])
        self.assertNotIn("docker-compose.forward.yml", frozen["files"])
        # the H-009 freeze keeps the shared compose and all three pairs
        self.assertIn("docker-compose.forward.yml", forward.tracked_files("H-009", self.root))
        self.assertEqual(forward.pair_keys("H-009", self.root), ["btc", "eth", "bnb"])

    def test_the_freeze_records_every_file_the_image_commit_and_the_exposure(self) -> None:
        frozen = self.freeze()
        self.assertEqual(frozen["image"], "freqtradeorg/freqtrade:2026.9")
        self.assertEqual(frozen["git_commit"], git(["rev-parse", "HEAD"], self.root).strip())
        self.assertEqual(frozen["exposure_by_pair"], {pair: 0.25 for pair in PAIR_NAMES.values()})
        self.assertEqual(frozen["strategy"]["class"], "Thing_H009_v1")
        self.assertEqual(set(frozen["files"]), set(forward.tracked_files("H-009", self.root)))
        self.assertIn("forward/config.h009.btc.json", frozen["files"])
        self.assertIn("user_data/config.dryrun.json", frozen["files"])  # the base config is part of what runs
        self.assertEqual(frozen["databases"]["ETH/USDT"], "user_data/tradesv3.forward.h009.eth.sqlite")
        self.assertIn("NÃO validada", frozen["label"])

    def test_an_unchanged_freeze_passes_the_check(self) -> None:
        self.freeze()
        git(["add", "-A"], self.root)
        git(["commit", "-q", "-m", "freeze"], self.root)
        self.assertEqual(forward.check_freeze("H-009", self.root), [])

    def test_changing_one_byte_of_any_frozen_file_fails_the_check(self) -> None:
        self.freeze()
        for name in ("forward/config.h009.bnb.json", "user_data/strategies/Thing_H009_v1.py", "docker-compose.forward.yml"):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            problems = forward.check_freeze("H-009", self.root)
            self.assertTrue(any(name in p for p in problems), (name, problems))
            path.write_bytes(original)
        self.assertEqual(forward.check_freeze("H-009", self.root), [])

    def test_an_uncommitted_frozen_file_is_refused_at_freeze_time(self) -> None:
        (self.root / "forward" / "config.h009.btc.json").write_text(json.dumps({"tradable_balance_ratio": 0.3}), encoding="utf-8")
        with self.assertRaises(ValueError):
            forward.build_freeze("H-009", self.root)

    def test_a_missing_freeze_or_missing_file_is_reported(self) -> None:
        self.assertTrue(any("no freeze record" in p for p in forward.check_freeze("H-009", self.root)))
        (self.root / "docker-compose.forward.yml").unlink()
        with self.assertRaises(FileNotFoundError):
            forward.build_freeze("H-009", self.root)

    def test_a_strategy_that_was_archived_cannot_be_frozen(self) -> None:
        (self.root / "user_data" / "strategies" / "Thing_H009_v1.py").unlink()
        with self.assertRaises(FileNotFoundError):
            forward.tracked_files("H-009", self.root)


def make_database(path: Path, trades: list[dict], orders: list[dict]) -> None:
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE trades (id INTEGER PRIMARY KEY, pair TEXT, is_open INTEGER, fee_open REAL, fee_close REAL,
        open_rate REAL, open_rate_requested REAL, close_rate REAL, close_rate_requested REAL, close_profit REAL,
        close_profit_abs REAL, stake_amount REAL, open_date TEXT, close_date TEXT, min_rate REAL, max_rate REAL, exit_reason TEXT)""")
    conn.execute("""CREATE TABLE orders (id INTEGER PRIMARY KEY, ft_trade_id INTEGER, ft_order_side TEXT, status TEXT,
        filled REAL, order_date TEXT, order_filled_date TEXT)""")
    for t in trades:
        conn.execute(f"INSERT INTO trades ({', '.join(t)}) VALUES ({', '.join('?' * len(t))})", list(t.values()))
    for o in orders:
        conn.execute(f"INSERT INTO orders ({', '.join(o)}) VALUES ({', '.join('?' * len(o))})", list(o.values()))
    conn.commit()
    conn.close()


CLOSED = {
    "pair": "BTC/USDT", "is_open": 0, "fee_open": 0.001, "fee_close": 0.001, "open_rate": 101.0, "open_rate_requested": 100.0,
    "close_rate": 109.0, "close_rate_requested": 110.0, "close_profit": 0.07, "close_profit_abs": 1.75, "stake_amount": 25.0,
    "open_date": "2026-11-01 10:00:00.000000", "close_date": "2026-11-03 10:00:00.000000", "min_rate": 99.0, "max_rate": 115.0,
    "exit_reason": "low72_or_regime_lost",
}
OPEN = {**CLOSED, "is_open": 1, "close_rate": None, "close_rate_requested": None, "close_profit": None, "close_profit_abs": None,
        "close_date": None, "exit_reason": None, "open_rate": 100.0}


class ReadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "bot.sqlite"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_a_missing_database_reads_as_empty(self) -> None:
        self.assertEqual(forward.read_database(self.db), ([], []))
        quality = forward.execution_quality([], [])
        self.assertEqual((quality["trades"], quality["entry_orders"]), (0, 0))
        self.assertIsNone(quality["entry_slippage_mean"])

    def test_the_database_is_opened_read_only(self) -> None:
        make_database(self.db, [CLOSED], [])
        conn = forward._connect_ro(self.db)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("DELETE FROM trades")
        conn.close()

    def test_closed_trades_become_backtest_shaped_and_open_ones_are_left_out(self) -> None:
        make_database(self.db, [CLOSED, OPEN], [])
        trades, _ = forward.read_database(self.db)
        shaped = forward.closed_as_backtest_trades(trades)
        self.assertEqual(len(shaped), 1)
        self.assertAlmostEqual(shaped[0]["profit_ratio"], 0.07)
        self.assertAlmostEqual(shaped[0]["trade_duration"], 2 * 24 * 60)
        # the same review that reads backtest exports reads the bot's trades
        review = tradereview.review(shaped)
        self.assertEqual(review["trades"], 1)
        self.assertEqual(review["exit_reasons"][0]["exit_reason"], "low72_or_regime_lost")

    def test_slippage_is_signed_against_what_the_bot_asked_for(self) -> None:
        make_database(self.db, [CLOSED], [])
        trades, orders = forward.read_database(self.db)
        quality = forward.execution_quality(trades, orders)
        self.assertAlmostEqual(quality["entry_slippage_mean"], 0.01)   # paid 101 for a requested 100: worse
        self.assertAlmostEqual(quality["exit_slippage_mean"], 1 - 109 / 110)  # sold at 109 for a requested 110: worse
        self.assertEqual((quality["closed"], quality["open"]), (1, 0))
        self.assertAlmostEqual(quality["observed_entry_cost_per_side_mean"], 0.001 + 0.01)
        self.assertEqual(quality["assumed_scenario"], "base")
        self.assertAlmostEqual(quality["assumed_cost_per_side"], 0.00175)

    def test_a_better_than_requested_fill_is_not_counted_as_cost(self) -> None:
        better = {**CLOSED, "open_rate": 99.0}
        quality = forward.execution_quality([better], [])
        self.assertAlmostEqual(quality["entry_slippage_mean"], -0.01)
        self.assertAlmostEqual(quality["observed_entry_cost_per_side_mean"], 0.001)  # only the fee

    def test_missed_entries_and_fill_latency_come_from_the_orders(self) -> None:
        orders = [
            {"ft_trade_id": 1, "ft_order_side": "buy", "status": "closed", "filled": 1.0, "order_date": "2026-11-01 10:00:00.000000", "order_filled_date": "2026-11-01 10:04:00.000000"},
            {"ft_trade_id": 2, "ft_order_side": "buy", "status": "canceled", "filled": 0.0, "order_date": "2026-11-02 10:00:00.000000", "order_filled_date": None},
            {"ft_trade_id": 1, "ft_order_side": "sell", "status": "closed", "filled": 1.0, "order_date": "2026-11-03 10:00:00.000000", "order_filled_date": "2026-11-03 10:01:00.000000"},
        ]
        make_database(self.db, [CLOSED], orders)
        trades, order_rows = forward.read_database(self.db)
        quality = forward.execution_quality(trades, order_rows)
        self.assertEqual((quality["entry_orders"], quality["entry_orders_not_filled"]), (2, 1))
        self.assertAlmostEqual(quality["fill_latency_minutes_mean"], 4.0)

    def test_the_report_has_the_label_and_hides_returns_unless_asked(self) -> None:
        frozen = {"label": forward.LABEL, "frozen_at_utc": "2026-11-04", "git_commit": "abcdef1234567", "image": "img", "rules": list(forward.RULES)}
        quality = forward.execution_quality([CLOSED], [])
        plain = forward.render_markdown("H-009", {"BTC/USDT": quality}, frozen)
        self.assertIn("NÃO validada", plain)
        self.assertNotIn("Retorno agregado", plain)
        self.assertIn("holdout", plain)
        shown = forward.render_markdown("H-009", {"BTC/USDT": quality}, frozen, {"BTC/USDT": {"closed": 1, "net_profit_abs": 1.75}})
        self.assertIn("monitoramento, NÃO avaliado", shown)


class RealFilesTests(unittest.TestCase):
    """The files the user will actually start."""

    def overlays(self) -> dict:
        return {key: json.loads((ROOT / forward.overlay_path("H-009", key)).read_text(encoding="utf-8")) for key in PAIR_NAMES}

    def test_each_overlay_runs_the_h009_strategy_on_its_own_pair_and_database(self) -> None:
        for key, overlay in self.overlays().items():
            self.assertEqual(overlay["strategy"], "WeeklyBreakoutRegime_H009_v1")
            self.assertEqual(overlay["exchange"]["pair_whitelist"], [PAIR_NAMES[key]])
            self.assertEqual(overlay["db_url"], "sqlite:///" + forward.database_path("H-009", key))
            self.assertEqual(overlay["bot_name"], f"forward-h009-{key}")

    def test_the_overlays_use_the_exposure_calibrated_for_h009_and_change_nothing_else_risky(self) -> None:
        conn = registry.connect()
        notes = registry.get_hypothesis(conn, "H-009")["notes"]
        calibrated = float(re.search(r"Calibrated exposure: ([0-9.]+)", notes).group(1))
        for overlay in self.overlays().values():
            self.assertEqual(overlay["tradable_balance_ratio"], calibrated)
            # nothing that could switch off dry-run, enable the API or add keys
            self.assertNotIn("dry_run", overlay)
            self.assertNotIn("api_server", overlay)
            self.assertEqual(set(overlay["exchange"]), {"pair_whitelist"})
            self.assertEqual(set(overlay), {"bot_name", "strategy", "db_url", "tradable_balance_ratio", "exchange"})

    def test_the_databases_do_not_collide_with_the_original_dry_run_database(self) -> None:
        names = {o["db_url"] for o in self.overlays().values()}
        self.assertEqual(len(names), 3)
        self.assertNotIn("sqlite:///user_data/tradesv3.dryrun.sqlite", names)

    def test_the_forward_compose_exposes_no_port_and_has_one_bot_per_pair(self) -> None:
        text = (ROOT / forward.COMPOSE).read_text(encoding="utf-8")
        self.assertNotIn("ports:", text)
        for forbidden in ("api_server", "8080", "--api", "dry_run: false", "dry-run false", "secret", "password"):
            self.assertNotIn(forbidden, text.lower())
        for key in PAIR_NAMES:
            self.assertIn(f"forward-h009-{key}:", text)
            self.assertIn(f"/freqtrade/forward/config.h009.{key}.json", text)
        self.assertIn("/freqtrade/forward:ro", text)  # overlays are mounted read-only
        self.assertEqual(forward.image_tag(ROOT), "freqtradeorg/freqtrade:2026.9")

    def test_the_h009_strategy_and_all_tracked_files_exist(self) -> None:
        for name in forward.tracked_files("H-009", ROOT):
            self.assertTrue((ROOT / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
