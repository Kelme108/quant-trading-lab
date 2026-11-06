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

    def test_a_candidate_reaches_a_frozen_started_dry_run_on_the_pairs_that_passed_validation(self) -> None:
        self.validation["BNB/USDT"] = "rejected"
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("dry-run started on BTC/USDT, ETH/USDT by the autopilot", text)
        self.assertEqual(self.read_calls, [("H-001", 0.2)])
        self.assertEqual(self.approvals("H-001"), [("validation", "autopilot-policy"), ("dryrun", "autopilot-policy")])
        self.assertEqual(self.started, ["docker-compose.forward.h001.yml"])
        frozen = json.loads(forward.freeze_path("H-001", self.root).read_text(encoding="utf-8"))
        self.assertEqual(frozen["exposure_by_pair"], {"BTC/USDT": 0.2, "ETH/USDT": 0.2})
        self.assertEqual(forward.check_freeze("H-001", self.root), [])
        compose = (self.root / "docker-compose.forward.h001.yml").read_text(encoding="utf-8")
        self.assertNotIn("bnb", compose)
        for forbidden in ("ports:", "8080", "api_server", "dry_run", "secret", "password"):
            self.assertNotIn(forbidden, compose.lower())
        for key in ("btc", "eth"):
            overlay = json.loads((self.root / forward.overlay_path("H-001", key)).read_text(encoding="utf-8"))
            self.assertEqual(set(overlay), {"bot_name", "strategy", "db_url", "tradable_balance_ratio", "exchange"})
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
        queue_idea(self.conn, 1)
        text = self.run_weekly()
        self.assertIn("bot cap would be exceeded", text)
        self.assertEqual(self.started, [])

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
