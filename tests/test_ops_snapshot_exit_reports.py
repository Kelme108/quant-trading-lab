"""ops/snapshot_exit_reports.py: tracked copy of the exit-menu reports, extended and never rewritten."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("snapshot_exit_reports", Path(__file__).resolve().parents[1] / "ops" / "snapshot_exit_reports.py")
snap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snap)


def _tree(root: Path, work_ledger: bytes, tracked_ledger: bytes):
    w, t = root / "ops/state/exit_menu", root / "research/b3/exit_menu"
    w.mkdir(parents=True), t.mkdir(parents=True)
    (w / "ledger.jsonl").write_bytes(work_ledger)
    (t / "ledger.jsonl").write_bytes(tracked_ledger)
    (w / "20261101T000000Z.json").write_text('{"run": "a"}', encoding="utf-8")
    (w / "20261102T000000Z.json").write_text('{"run": "b"}', encoding="utf-8")
    (t / "20261101T000000Z.json").write_text('{"run": "a"}', encoding="utf-8")
    return w, t


def test_copies_new_reports_and_extends_the_ledger(tmp_path):
    w, t = _tree(tmp_path, b"1\n2\n3\n", b"1\n2\n")
    out = snap.snapshot(tmp_path, lock=None)
    assert out["copied"] == ["research/b3/exit_menu/20261102T000000Z.json"]
    assert out["ledgers"] == ["research/b3/exit_menu/ledger.jsonl"]
    assert (t / "ledger.jsonl").read_bytes() == b"1\n2\n3\n"
    assert (t / "20261102T000000Z.json").read_text(encoding="utf-8") == '{"run": "b"}'


def test_dry_run_changes_nothing(tmp_path):
    w, t = _tree(tmp_path, b"1\n2\n3\n", b"1\n2\n")
    out = snap.snapshot(tmp_path, dry_run=True, lock=None)
    assert out["copied"] and out["ledgers"]
    assert (t / "ledger.jsonl").read_bytes() == b"1\n2\n" and not (t / "20261102T000000Z.json").exists()


def test_refuses_a_rewritten_ledger(tmp_path):
    w, t = _tree(tmp_path, b"X\n2\n3\n", b"1\n2\n")
    with pytest.raises(RuntimeError, match="not a prefix"):
        snap.snapshot(tmp_path, lock=None)
    assert (t / "ledger.jsonl").read_bytes() == b"1\n2\n"


def test_refuses_a_report_that_changed(tmp_path):
    w, t = _tree(tmp_path, b"1\n", b"1\n")
    (t / "20261101T000000Z.json").write_text('{"run": "edited"}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="different content"):
        snap.snapshot(tmp_path, lock=None)


def test_waits_for_a_running_cycle(tmp_path):
    _tree(tmp_path, b"1\n", b"1\n")
    lock = tmp_path / "cycle.lock"
    lock.write_text("123", encoding="utf-8")
    with pytest.raises(RuntimeError, match="holds"):
        snap.snapshot(tmp_path, lock=lock)
