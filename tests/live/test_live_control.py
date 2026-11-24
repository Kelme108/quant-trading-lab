"""Operator commands (close / pause / resume / close_stop) executed by the engine itself."""

from live.core.control import Control, write_command
from live.core.engine import Engine
from live_helpers import SCENARIO_A, SYMBOL, Rig


def rig_with_control(tmp_path, closes=SCENARIO_A):
    rig = Rig(tmp_path, closes)
    path = tmp_path / "commands" / "bot.json"
    rig.cmd_path = path
    mk = lambda: Engine(rig.broker, rig.strategy, rig.clock, rig.cal, rig.journal, rig.risk, rig.ks,  # noqa: E731
                        [SYMBOL], volume=1.0, alert=rig.alerts.append, control=Control(path))
    rig.new_engine = mk
    rig.engine = mk()
    rig.engine.start()
    return rig


def test_close_goes_through_the_journal_and_the_robot_keeps_running(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    assert rig.broker.positions()
    write_command(rig.cmd_path, "close", "c1")
    assert "command:close" in rig.engine.step()
    assert rig.broker.positions() == [] and rig.journal.net_volume(SYMBOL) == 0
    assert not rig.engine.safe_mode                                   # journal and broker agree: no safe mode
    assert [f["reason"] for f in rig.kinds("fill")][-1] == "manual_close"
    (cmd,) = rig.kinds("command")
    assert (cmd["key"], cmd["action"], cmd["result"]) == ("c1", "close", "closed")
    assert not rig.cmd_path.exists() and not rig.engine.paused


def test_close_with_nothing_open_says_so(tmp_path):
    rig = rig_with_control(tmp_path)
    write_command(rig.cmd_path, "close", "c1")
    rig.engine.step()
    assert rig.kinds("command")[0]["result"] == "nothing_to_close"


def test_close_works_even_in_safe_mode(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    rig.engine._sticky_safe = True
    write_command(rig.cmd_path, "close", "c1")
    assert rig.engine.step() == ["command:close", "safe_mode"]
    assert rig.broker.positions() == []


def test_pause_blocks_entries_and_survives_a_restart(tmp_path):
    rig = rig_with_control(tmp_path)
    write_command(rig.cmd_path, "pause", "p1")
    rig.run(2, 5)                                                      # the rule signals an entry after bar 4
    assert rig.kinds("order_sent") == [] and rig.engine.paused
    assert any("paused" in v["reasons"] for v in rig.kinds("veto"))
    rig.engine = rig.new_engine()                                      # process restart
    rig.engine.start()
    assert rig.engine.paused
    write_command(rig.cmd_path, "resume", "r1")
    rig.engine.step()
    assert not rig.engine.paused
    rig.engine = rig.new_engine()
    rig.engine.start()
    assert not rig.engine.paused


def test_pause_still_lets_an_open_position_exit(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    assert rig.broker.positions()
    write_command(rig.cmd_path, "pause", "p1")
    rig.run(6, 7)                                                      # the rule's own exit after bar 6
    assert rig.broker.positions() == []
    assert [e["side"] for e in rig.kinds("order_sent")] == ["buy", "sell"]


def test_close_stop_flattens_and_pauses(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    write_command(rig.cmd_path, "close_stop", "s1")
    rig.engine.step()
    assert rig.broker.positions() == [] and rig.engine.paused
    assert rig.kinds("command")[0]["result"] == "closed+paused"


def test_a_command_id_runs_once(tmp_path):
    rig = rig_with_control(tmp_path)
    write_command(rig.cmd_path, "pause", "p1")
    rig.engine.step()
    write_command(rig.cmd_path, "pause", "p1")                         # the file came back (crash before deleting)
    rig.engine.step()
    assert len(rig.kinds("command")) == 1 and len(rig.kinds("pause")) == 1
    assert not rig.cmd_path.exists()


def test_malformed_or_unknown_commands_are_ignored(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    rig.cmd_path.parent.mkdir(parents=True, exist_ok=True)
    for text in ("not json", '{"id": "x", "action": "liquidate"}', '{"action": "close"}', "[]"):
        rig.cmd_path.write_text(text, encoding="utf-8")
        rig.engine.step()
    assert rig.broker.positions() and rig.kinds("command") == []


def test_the_kill_switch_still_wins(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.ks.trigger("stop")
    write_command(rig.cmd_path, "resume", "r1")
    assert rig.engine.step() == ["killswitch"] and rig.kinds("command") == []


def test_stop_flattens_journals_and_asks_the_loop_to_leave(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    assert rig.broker.positions() and not rig.engine.stopped
    write_command(rig.cmd_path, "stop", "x1")
    rig.engine.step()
    assert rig.broker.positions() == [] and rig.engine.stopped and not rig.engine.paused
    assert rig.kinds("command")[0]["result"] == "closed+stopped" and len(rig.kinds("stop")) == 1


def test_stop_without_a_position_just_stops(tmp_path):
    rig = rig_with_control(tmp_path)
    write_command(rig.cmd_path, "stop", "x1")
    rig.engine.step()
    assert rig.engine.stopped and rig.kinds("command")[0]["result"] == "nothing_to_close+stopped"


def test_stop_does_not_leave_while_a_position_could_not_be_closed(tmp_path):
    rig = rig_with_control(tmp_path)
    rig.run(2, 5)
    rig.broker.close_all = lambda reason="": None                 # the broker silently fails to close
    write_command(rig.cmd_path, "stop", "x1")
    rig.engine.step()
    assert not rig.engine.stopped and rig.broker.positions()
    assert rig.kinds("command")[0]["result"] == "close_failed" and rig.alerts
