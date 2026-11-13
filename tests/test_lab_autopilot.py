import functools
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from lab import autopilot, forward, registry  # noqa: E402
from test_lab_orchestrator import PAIRS, git  # noqa: E402
from test_lab_pipeline import PipelineTestCase, queue_idea  # noqa: E402

import pin_pairs  # noqa: E402

setUpModule, tearDownModule = pin_pairs.module_fixtures()


POLICY = {
    "enabled": True, "auto_validation": True, "auto_dryrun": True, "real_money": False,
    "min_stake_quote": 10.0, "wallet_quote": 100.0, "max_forward_bots": 12,
    "approved_by": "owner", "approved_at_utc": "2026-11-06T00:00:00+00:00", "note": "test",
}


class ShippedPolicyTests(unittest.TestCase):
    def test_the_shipped_policy_reaches_dry_run_and_never_real_money(self) -> None:
        policy = autopilot.load_policy()
        self.assertIs(policy["real_money"], False)
        self.assertTrue(policy["enabled"] and policy["auto_validation"] and policy["auto_dryrun"])

    def test_a_policy_that_allows_real_money_is_refused(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "autopilot.json"
            for bad in (True, "true", None, 1):
                path.write_text(json.dumps({**POLICY, "real_money": bad}), encoding="utf-8")
                with self.assertRaises(autopilot.PolicyError):
                    autopilot.load_policy(path)

    def test_no_agent_may_write_the_policy(self) -> None:
        from lab import guard
        for patterns in guard.AGENT_ALLOWED_PATHS.values():
            self.assertFalse(any("lab/" in p for p in patterns), patterns)


class ForwardFilesTests(unittest.TestCase):
    """The files the generator writes, for both layouts, without the pipeline."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_multi_pair_is_the_default_one_overlay_one_service_same_stake_per_pair(self) -> None:
        pairs = list(forward.PAIR_KEYS.values())
        written = autopilot.write_forward_files("H-105", pairs, 0.25, "Thing_H105_v1", self.root, wallet_quote=1000.0)
        self.assertEqual(written, ["forward/config.h105.json", "docker-compose.forward.h105.yml"])
        overlay = json.loads((self.root / "forward" / "config.h105.json").read_text(encoding="utf-8"))
        self.assertEqual(overlay, {
            "bot_name": "forward-h105", "strategy": "Thing_H105_v1", "db_url": "sqlite:///user_data/tradesv3.forward.h105.sqlite",
            "max_open_trades": len(pairs), "stake_amount": "unlimited", "tradable_balance_ratio": 0.25, "dry_run_wallet": 1000.0 * len(pairs),
            "exchange": {"pair_whitelist": pairs}})
        # Freqtrade's unlimited stake: (wallet + closed profit) x ratio / max_open_trades
        self.assertEqual(overlay["dry_run_wallet"] * overlay["tradable_balance_ratio"] / overlay["max_open_trades"], 1000.0 * 0.25)
        for forbidden in ("dry_run\"", "api_server", "key", "secret", "password"):
            self.assertNotIn(forbidden, json.dumps(overlay).replace("dry_run_wallet", ""))
        compose = (self.root / "docker-compose.forward.h105.yml").read_text(encoding="utf-8")
        self.assertEqual(compose.count("container_name:"), 1)
        self.assertIn("  forward-h105:\n", compose)
        self.assertIn("--config /freqtrade/forward/config.h105.json", compose)
        self.assertIn("--logfile /freqtrade/user_data/logs/forward-h105.log", compose)
        self.assertIn("/freqtrade/forward:ro", compose)
        for forbidden in ("ports:", "8080", "api_server", "dry_run", "secret", "password"):
            self.assertNotIn(forbidden, compose.lower())
        self.assertEqual(forward.layout("H-105", self.root), forward.MULTI_PAIR)
        self.assertEqual(len(forward.pair_keys("H-105", self.root)), len(forward.PAIR_KEYS))

    def test_the_per_pair_layout_writes_the_same_bytes_as_before(self) -> None:
        written = autopilot.write_forward_files("H-104", ["BNB/USDT", "ETH/USDT"], 0.25, "HourlyWilliamsVolBreakoutRVol_H104_v1",
                                                self.root, wallet_quote=1000.0, layout=forward.PER_PAIR)
        self.assertEqual(written, ["forward/config.h104.bnb.json", "forward/config.h104.eth.json", "docker-compose.forward.h104.yml"])
        # The bytes the per-pair generator wrote for the old H-104 freeze (git 559e6d3^); a literal, so the test does not depend on
        # which hypotheses are frozen in the repository today.
        self.assertEqual((self.root / "forward/config.h104.bnb.json").read_text(encoding="utf-8"), (
            '{\n  "bot_name": "forward-h104-bnb",\n  "strategy": "HourlyWilliamsVolBreakoutRVol_H104_v1",\n'
            '  "db_url": "sqlite:///user_data/tradesv3.forward.h104.bnb.sqlite",\n  "tradable_balance_ratio": 0.25,\n'
            '  "dry_run_wallet": 1000.0,\n  "exchange": {\n    "pair_whitelist": [\n      "BNB/USDT"\n    ]\n  }\n}\n'))
        compose = (self.root / "docker-compose.forward.h104.yml").read_text(encoding="utf-8")
        self.assertEqual(compose.count("container_name:"), 2)
        self.assertIn("container_name: forward-h104-bnb\n", compose)
        self.assertIn("--config /freqtrade/forward/config.h104.eth.json", compose)

    def test_an_unknown_layout_or_pair_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            autopilot.write_forward_files("H-105", ["BTC/USDT"], 0.25, "X", self.root, layout="weird")
        with self.assertRaises(KeyError):
            autopilot.write_forward_files("H-105", ["EVIL/USDT"], 0.25, "X", self.root)
        self.assertFalse((self.root / "forward").exists())

    def test_containers_are_counted_one_per_multi_pair_bot(self) -> None:
        folder = self.root / "research" / "forward"
        folder.mkdir(parents=True)
        (folder / "H-001-freeze.json").write_text(json.dumps({"databases": {"BTC/USDT": "a", "ETH/USDT": "b", "BNB/USDT": "c"}}), encoding="utf-8")
        (folder / "H-105-freeze.json").write_text(json.dumps({"layout": forward.MULTI_PAIR,
                                                              "databases": {p: "x" for p in forward.PAIR_KEYS.values()}}), encoding="utf-8")
        self.assertEqual(autopilot.running_forward_bots(self.root), 4)
        self.assertEqual(autopilot.running_forward_pairs(self.root), 3 + len(forward.PAIR_KEYS))

    def test_the_shipped_bots_never_count_more_containers_than_pairs(self) -> None:
        # per-pair bots: one container per pair; multi-pair bots: one container for several pairs
        self.assertLessEqual(autopilot.running_forward_bots(ROOT), autopilot.running_forward_pairs(ROOT))


class AutopilotPipelineTests(PipelineTestCase):
    """A candidate goes through validation to a frozen, started dry-run with no per-hypothesis approval."""

    def setUp(self) -> None:
        super().setUp()
        self.validation = {p: "candidate_for_portfolio" for p in PAIRS}
        self.read_calls: list[tuple[str, float]] = []
        self.started: list[str] = []
        self.exposure = 0.2
        original = self.fake_explore

        def explore_with_exposure(conn, hid, **kwargs):
            out = original(conn, hid, **kwargs)
            conn.execute("UPDATE hypotheses SET notes = COALESCE(notes,'') || ? WHERE id = ?",
                         (f" Calibrated exposure: {self.exposure} (p95 by pair {{}}).", hid))
            conn.commit()
            return out

        self.fake_explore = explore_with_exposure
        self.pipe = self.make_pipeline()
        self.pipe.autopilot = functools.partial(
            autopilot.run, commit=self.pipe._commit, root=self.root, policy=dict(POLICY),
            read=self.fake_read, start=self.fake_start, pairs=list(PAIRS),
        )

    def fake_read(self, conn, hid, exposure, *, root, pairs):
        self.read_calls.append((hid, exposure))
        self.assertTrue(registry.has_approval(conn, hid, "validation"))
        return dict(self.validation)

    def fake_start(self, compose, root):
        self.started.append(compose)
        return True, "started"

    def approvals(self, hid: str) -> list[tuple[str, str]]:
        return [(r["stage"], r["approved_by"]) for r in
                self.conn.execute("SELECT stage, approved_by FROM approvals WHERE hypothesis_id = ? ORDER BY id", (hid,))]

    def test_a_candidate_reaches_one_frozen_started_multi_pair_bot_on_the_pairs_that_passed_validation(self) -> None:
        self.validation["BNB/USDT"] = "rejected"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("dry-run started on BTC/USDT, ETH/USDT by the autopilot", text)
        self.assertEqual(self.read_calls, [("H-001", 0.2)])
        self.assertEqual(self.approvals("H-001"), [("validation", "autopilot-policy"), ("dryrun", "autopilot-policy")])
        self.assertEqual(self.started, ["docker-compose.forward.h001.yml"])
        frozen = json.loads(forward.freeze_path("H-001", self.root).read_text(encoding="utf-8"))
        self.assertEqual(frozen["layout"], forward.MULTI_PAIR)
        self.assertEqual(frozen["exposure_by_pair"], {"BTC/USDT": 0.2, "ETH/USDT": 0.2})
        self.assertEqual(frozen["bot"]["container"], "forward-h001")
        self.assertEqual(forward.check_freeze("H-001", self.root), [])
        self.assertEqual(autopilot.running_forward_bots(self.root), 1)
        self.assertEqual(autopilot.running_forward_pairs(self.root), 2)
        compose = (self.root / "docker-compose.forward.h001.yml").read_text(encoding="utf-8")
        self.assertNotIn("bnb", compose)
        self.assertEqual(compose.count("container_name:"), 1)
        self.assertIn("container_name: forward-h001\n", compose)
        self.assertIn("/freqtrade/forward/config.h001.json", compose)
        for forbidden in ("ports:", "8080", "api_server", "dry_run", "secret", "password"):
            self.assertNotIn(forbidden, compose.lower())
        overlay = json.loads((self.root / forward.multi_overlay_path("H-001")).read_text(encoding="utf-8"))
        self.assertEqual(overlay["exchange"], {"pair_whitelist": ["BTC/USDT", "ETH/USDT"]})
        self.assertEqual((overlay["max_open_trades"], overlay["dry_run_wallet"]), (2, 200.0))  # 2 x the test wallet_quote
        self.assertFalse((self.root / forward.overlay_path("H-001", "btc")).exists())
        self.assertEqual(git(["status", "--porcelain", "--", "forward", "research/forward", "docker-compose.forward.h001.yml"],
                             self.root).strip(), "")

    def test_the_old_per_pair_layout_still_works_on_request(self) -> None:
        self.pipe.autopilot.keywords["layout"] = forward.PER_PAIR
        self.validation["BNB/USDT"] = "rejected"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("dry-run started on BTC/USDT, ETH/USDT by the autopilot", text)
        frozen = json.loads(forward.freeze_path("H-001", self.root).read_text(encoding="utf-8"))
        self.assertNotIn("layout", frozen)
        self.assertEqual(frozen["exposure_by_pair"], {"BTC/USDT": 0.2, "ETH/USDT": 0.2})
        self.assertEqual(forward.check_freeze("H-001", self.root), [])
        self.assertEqual(autopilot.running_forward_bots(self.root), 2)
        compose = (self.root / "docker-compose.forward.h001.yml").read_text(encoding="utf-8")
        self.assertNotIn("bnb", compose)
        for forbidden in ("ports:", "8080", "api_server", "dry_run", "secret", "password"):
            self.assertNotIn(forbidden, compose.lower())
        for key in ("btc", "eth"):
            overlay = json.loads((self.root / forward.overlay_path("H-001", key)).read_text(encoding="utf-8"))
            self.assertEqual(set(overlay), {"bot_name", "strategy", "db_url", "tradable_balance_ratio", "dry_run_wallet", "exchange"})
            self.assertEqual(overlay["dry_run_wallet"], 100.0)  # the test policy's wallet_quote
        self.assertEqual(git(["status", "--porcelain", "--", "forward", "research/forward", "docker-compose.forward.h001.yml"],
                             self.root).strip(), "")
        self.assertNotIn("approve.py H-001 --stage validation", text)

    def test_no_pair_passing_validation_means_no_bot(self) -> None:
        self.validation = {p: "inconclusive" for p in PAIRS}
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("validation read by the autopilot: no pair passed", text)
        self.assertEqual(self.started, [])
        self.assertFalse(forward.freeze_path("H-001", self.root).exists())
        self.assertEqual(self.approvals("H-001"), [("validation", "autopilot-policy")])

    def test_one_pair_passing_validation_is_too_few_for_the_breadth_rule(self) -> None:
        self.validation = {p: "rejected" for p in PAIRS}
        self.validation["ETH/USDT"] = "candidate_for_portfolio"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("validation read by the autopilot: too few pairs passed (ETH/USDT; the breadth rule needs 2)", text)
        self.assertEqual(self.started, [])
        self.assertFalse(forward.freeze_path("H-001", self.root).exists())

    def test_a_stake_below_the_minimum_order_gets_no_bot(self) -> None:
        self.exposure = 0.05
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("below the minimum order", text)
        self.assertEqual(self.started, [])

    def test_the_bot_cap_stops_before_freezing(self) -> None:
        self.pipe.autopilot.keywords["policy"]["max_forward_bots"] = 2
        self.pipe.autopilot.keywords["layout"] = forward.PER_PAIR   # 3 containers > 2
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("bot cap would be exceeded", text)
        self.assertEqual(self.started, [])

    def test_a_multi_pair_bot_counts_as_one_bot_under_the_cap(self) -> None:
        self.write_freeze("H-900", {"databases": {"BTC/USDT": "a"}})   # one older per-pair bot
        self.pipe.autopilot.keywords["policy"]["max_forward_bots"] = 2
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("dry-run started on BTC/USDT, ETH/USDT, BNB/USDT by the autopilot", text)
        self.assertEqual(autopilot.running_forward_bots(self.root), 2)

    def test_the_cap_still_stops_a_multi_pair_bot_when_it_is_full(self) -> None:
        self.write_freeze("H-900", {"databases": {"BTC/USDT": "a", "ETH/USDT": "b"}})
        self.pipe.autopilot.keywords["policy"]["max_forward_bots"] = 2
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("bot cap would be exceeded", text)
        self.assertEqual(self.started, [])

    def write_freeze(self, hid: str, record: dict) -> None:
        path = self.root / "research" / "forward" / f"{hid}-freeze.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")
        git(["add", "-A"], self.root)
        git(["commit", "-q", "-m", f"{hid} freeze"], self.root)

    def test_policy_off_leaves_the_candidate_waiting_for_the_user(self) -> None:
        self.pipe.autopilot.keywords["policy"]["enabled"] = False
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("candidate: awaiting the user's approval", text)
        self.assertIn("approve.py H-001 --stage validation", text)
        self.assertEqual(self.read_calls, [])

    def test_a_rejected_exploration_never_reaches_the_autopilot(self) -> None:
        self.experiments.decision = "rejected"
        queue_idea(self.conn, 1)
        self.run_weekly()
        self.assertEqual(self.read_calls, [])
        self.assertEqual(self.started, [])


if __name__ == "__main__":
    unittest.main()
