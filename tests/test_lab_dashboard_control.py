"""POST /api/control (the real-account section's buttons): who may call it, and what it writes."""

import http.client
import json
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path

from lab import dashboard

CFG = {"mode": "live", "symbols": ["WINZ26"], "strategy": {"rule": "P-004", "market": "WIN"},
       "journal_db": "live/journal.live-b3-win.sqlite", "feed_file": "live/state/feed-live-b3-win.json"}


class ControlEndpoint(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name)
        (self.root / "live" / "config").mkdir(parents=True)
        (self.root / "live" / "config" / "live-b3-win.json").write_text(json.dumps(CFG), encoding="utf-8")
        (self.root / "live" / "config" / "demo-b3-win.json").write_text(json.dumps({**CFG, "mode": "demo"}), encoding="utf-8")
        self.feed = self.root / "live" / "state" / "feed-live-b3-win.json"
        self.feed.parent.mkdir(parents=True)
        self.fresh_feed()
        self.server = dashboard.create_server(lambda: {}, 0, root=self.root)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.cmd = self.root / "live" / "commands" / "live-b3-win.json"

    def fresh_feed(self) -> None:
        self.feed.write_text(json.dumps({"updated_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def call(self, method, path, body=None, headers=None, raw=None):
        h = {"Host": f"127.0.0.1:{self.port}", "Origin": f"http://127.0.0.1:{self.port}",
             "X-Control-Token": self.server.control_token, "Content-Type": "application/json"}
        h.update(headers or {})
        h = {k: v for k, v in h.items() if v is not None}
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
            data = raw if raw is not None else (json.dumps(body).encode() if body is not None else b"")
            for k, v in h.items():
                conn.putheader(k, v)
            conn.putheader("Content-Length", str(len(data)))
            conn.endheaders(data)
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def post(self, body, **kw):
        return self.call("POST", "/api/control", body, **kw)

    def test_a_valid_command_writes_the_file_and_a_second_one_waits(self):
        status, out = self.post({"id": "live-b3-win", "action": "close"})
        self.assertEqual(status, 202, out)
        cmd = json.loads(self.cmd.read_text(encoding="utf-8"))
        self.assertEqual((cmd["action"], cmd["id"], cmd["source"]), ("close", json.loads(out)["id"], "portal"))
        self.assertEqual(self.post({"id": "live-b3-win", "action": "pause"})[0], 409)
        self.assertEqual(json.loads(self.cmd.read_text(encoding="utf-8"))["action"], "close")

    def test_all_command_actions_are_accepted(self):
        for action in ("close", "pause", "resume", "close_stop", "stop"):
            self.assertEqual(self.post({"id": "live-b3-win", "action": action})[0], 202, action)
            self.cmd.unlink()

    def test_the_token_the_origin_and_the_host_are_all_required(self):
        ok = {"id": "live-b3-win", "action": "close"}
        self.assertEqual(self.post(ok, headers={"X-Control-Token": None})[0], 403)
        self.assertEqual(self.post(ok, headers={"X-Control-Token": "wrong"})[0], 403)
        self.assertEqual(self.post(ok, headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.post(ok, headers={"Origin": None})[0], 403)
        self.assertEqual(self.post(ok, headers={"Host": f"evil.example:{self.port}"})[0], 403)
        self.assertFalse(self.cmd.exists())

    def test_only_json_small_bodies_with_known_robot_and_action(self):
        self.assertEqual(self.post({"id": "live-b3-win", "action": "close"}, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.post(None, raw=b"not json")[0], 400)
        self.assertEqual(self.post(None, raw=b"{" + b" " * 600 + b"}")[0], 400)
        self.assertEqual(self.post({"id": "live-b3-win", "action": "liquidate"})[0], 400)
        self.assertEqual(self.post({"id": "live-b3-nope", "action": "close"})[0], 404)
        for bad in ("demo-b3-win", "live-b3-../x", "../live-b3-win", "live-b3-WIN", "live-b3-"):
            self.assertEqual(self.post({"id": bad, "action": "close"})[0], 400, bad)
        self.assertFalse(self.cmd.exists())

    def test_a_command_for_a_robot_that_is_not_running_is_refused(self):
        self.feed.write_text(json.dumps({"updated_at": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")
        for action in ("close", "pause", "stop"):
            self.assertEqual(self.post({"id": "live-b3-win", "action": action})[0], 409, action)
        self.assertFalse(self.cmd.exists())

    def test_start_launches_the_process_and_records_its_pid(self):
        class Fake:
            pid = 4242

            def poll(self):
                return None
        calls = []
        self.server.spawn = lambda root, rid: calls.append(rid) or Fake()
        self.feed.write_text(json.dumps({"updated_at": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")   # not running
        self.cmd.parent.mkdir(parents=True)
        self.cmd.write_text("{}", encoding="utf-8")                                                       # stale command
        status, out = self.post({"id": "live-b3-win", "action": "start"})
        self.assertEqual((status, json.loads(out)["pid"]), (202, 4242), out)
        self.assertEqual(calls, ["live-b3-win"])
        self.assertEqual((self.root / "live" / "state" / "live-b3-win.pid").read_text(encoding="utf-8"), "4242")
        self.assertFalse(self.cmd.exists())

    def test_start_reports_why_a_robot_dies_at_once_and_refuses_a_running_one(self):
        class Dead:
            pid = 4243

            def poll(self):
                return 3
        logs = self.root / "live" / "logs"
        logs.mkdir(parents=True)
        (logs / "live-b3-win-task.log").write_text("boom\nrefusing to trade: ['no_real_account']\n", encoding="utf-8")
        self.server.spawn = lambda root, rid: Dead()
        self.feed.write_text(json.dumps({"updated_at": "2020-01-01T00:00:00+00:00"}), encoding="utf-8")
        status, out = self.post({"id": "live-b3-win", "action": "start"})
        self.assertEqual(status, 500)
        self.assertIn("no_real_account", json.loads(out)["detail"])
        self.assertFalse((self.root / "live" / "state" / "live-b3-win.pid").exists())
        self.fresh_feed()
        self.assertEqual(self.post({"id": "live-b3-win", "action": "start"})[0], 409)       # already running

    def test_the_demo_robots_cannot_be_commanded_from_the_portal(self):
        self.assertEqual(self.post({"id": "demo-b3-win", "action": "close"})[0], 400)
        self.assertFalse((self.root / "live" / "commands" / "demo-b3-win.json").exists())

    def test_a_command_file_outside_live_commands_is_refused(self):
        (self.root / "live" / "config" / "live-b3-win.json").write_text(
            json.dumps({**CFG, "command_file": "live/config/oops.json"}), encoding="utf-8")
        self.assertEqual(self.post({"id": "live-b3-win", "action": "close"})[0], 400)

    def test_other_methods_and_paths_stay_read_only(self):
        self.assertEqual(self.call("POST", "/api/state", {"x": 1})[0], 405)
        self.assertEqual(self.call("PUT", "/api/control", {"x": 1})[0], 405)
        self.assertEqual(self.call("GET", "/api/control")[0], 404)

    def test_the_token_is_served_with_the_live_state_and_differs_per_server(self):
        status, out = self.call("GET", "/api/real-b3")
        self.assertEqual(status, 200)
        state = json.loads(out)
        self.assertEqual(state["control_token"], self.server.control_token)
        self.assertEqual([i["id"] for i in state["items"]], ["live-b3-win"])    # demo configs are not listed
        self.assertTrue(state["items"][0]["mode"] == "live" and state["items"][0]["paused"] is False)
        other = dashboard.create_server(lambda: {}, 0, root=self.root)
        try:
            self.assertNotEqual(other.control_token, self.server.control_token)
        finally:
            other.server_close()


if __name__ == "__main__":
    unittest.main()
