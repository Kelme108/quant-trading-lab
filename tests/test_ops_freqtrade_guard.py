"""ops/freqtrade_guard.py: health, portfolio loss limits and the kill switch, with a fake docker."""

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "ops"))
import freqtrade_guard as guard  # noqa: E402

UTC = timezone.utc
NOW = datetime(2026, 11, 6, 15, 0, tzinfo=UTC)


def make_db(path: Path, trades: list[tuple[int, float | None, str | None]]) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE trades(id INTEGER PRIMARY KEY, is_open INTEGER, close_profit_abs REAL, close_date TEXT)")
    con.executemany("INSERT INTO trades(is_open, close_profit_abs, close_date) VALUES(?,?,?)", trades)
    con.commit()
    con.close()


def make_log(path: Path, last: datetime | None) -> None:
    lines = ["2026-11-06 10:00:00,001 - freqtrade.worker - INFO - something else"]
    if last:
        lines.append(f"{last:%Y-%m-%d %H:%M:%S},017 - freqtrade.worker - INFO - Bot heartbeat. PID=1, state='RUNNING'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class FakeDocker:
    def __init__(self, running: dict[str, bool]):
        self.running, self.calls = dict(running), []

    def __call__(self, args):
        self.calls.append(args)
        if args[0] == "inspect":
            name = args[-1]
            return (0, "true" if self.running.get(name) else "false") if name in self.running else (1, "No such container")
        if args[0] == "stop":
            self.running[args[1]] = False
            return 0, args[1]
        return 1, "?"


def setup(tmp_path, trades_a, trades_b, limits=None, enforce=False, hb=NOW - timedelta(minutes=1)):
    make_db(tmp_path / "a.sqlite", trades_a)
    make_db(tmp_path / "b.sqlite", trades_b)
    make_log(tmp_path / "a.log", hb)
    make_log(tmp_path / "b.log", hb)
    cfg = {"name": "t", "enforce": enforce, "heartbeat_max_minutes": 5, "since_utc": "2026-11-01T00:00:00+00:00",
           "limits": limits or {}, "stop_file": str(tmp_path / "STOP"),
           "status_file": str(tmp_path / "status.json"), "alerts_log": str(tmp_path / "alerts.log"),
           "bots": [{"name": n, "container": n, "db": str(tmp_path / f"{n}.sqlite"), "log": str(tmp_path / f"{n}.log")}
                    for n in ("a", "b")]}
    path = tmp_path / "guard.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


TODAY = "2026-11-06 09:00:00"
YESTERDAY = "2026-11-05 09:00:00"


def test_healthy_and_within_limits_is_ok(tmp_path):
    path = setup(tmp_path, [(0, -1.0, TODAY), (1, None, None)], [(0, 2.0, YESTERDAY)],
                 limits={"max_daily_loss": 5, "max_total_loss": 10})
    docker = FakeDocker({"a": True, "b": True})
    assert guard.main(["--config", str(path)], docker=docker, now=NOW) == 0
    status = json.loads((tmp_path / "status.json").read_text())
    assert status["realized_today"] == -1.0 and status["realized_total"] == 1.0
    assert status["bots"][0]["open_trades"] == 1
    assert not any(c[0] == "stop" for c in docker.calls)


def test_daily_loss_is_summed_across_bots_and_enforced(tmp_path):
    path = setup(tmp_path, [(0, -3.0, TODAY)], [(0, -2.5, TODAY), (0, 50.0, YESTERDAY)],
                 limits={"max_daily_loss": 5, "max_total_loss": 100}, enforce=True)
    docker = FakeDocker({"a": True, "b": True})
    assert guard.main(["--config", str(path)], docker=docker, now=NOW) == 2
    assert ["stop", "a"] in docker.calls and ["stop", "b"] in docker.calls
    assert (tmp_path / "STOP").exists() and "daily loss" in (tmp_path / "STOP").read_text()
    assert json.loads((tmp_path / "status.json").read_text())["stopped"] is True


def test_breach_without_enforce_only_reports(tmp_path):
    path = setup(tmp_path, [(0, -30.0, YESTERDAY)], [], limits={"max_total_loss": 10})
    docker = FakeDocker({"a": True, "b": True})
    assert guard.main(["--config", str(path)], docker=docker, now=NOW) == 2
    assert not any(c[0] == "stop" for c in docker.calls) and not (tmp_path / "STOP").exists()
    assert "report only" in (tmp_path / "alerts.log").read_text()


def test_stop_file_is_a_manual_kill_switch(tmp_path):
    path = setup(tmp_path, [], [], enforce=True)
    (tmp_path / "STOP").write_text("operator: manual stop")
    docker = FakeDocker({"a": True, "b": True})
    assert guard.main(["--config", str(path)], docker=docker, now=NOW) == 2
    assert docker.running == {"a": False, "b": False}
    assert (tmp_path / "STOP").read_text() == "operator: manual stop"    # never overwritten


def test_dead_container_and_stale_heartbeat_are_reported(tmp_path):
    path = setup(tmp_path, [], [], hb=NOW - timedelta(minutes=30))
    docker = FakeDocker({"a": False, "b": True})
    assert guard.main(["--config", str(path)], docker=docker, now=NOW) == 1
    alerts = (tmp_path / "alerts.log").read_text()
    assert "a: container not running" in alerts and "b: no heartbeat" in alerts


def test_missing_database_counts_as_zero(tmp_path):
    path = setup(tmp_path, [], [])
    (tmp_path / "a.sqlite").unlink()
    assert guard.main(["--config", str(path)], docker=FakeDocker({"a": True, "b": True}), now=NOW) == 0


def test_shipped_guard_configs_are_valid():
    for name in ("guard.forward.json", "guard.testnet.json"):
        cfg = json.loads((ROOT / "ops" / name).read_text(encoding="utf-8"))
        assert cfg["bots"] and all({"name", "container", "db", "log"} <= set(b) for b in cfg["bots"])
    forward = json.loads((ROOT / "ops" / "guard.forward.json").read_text(encoding="utf-8"))
    assert forward["enforce"] is False      # a frozen forward test is only stopped by the user
