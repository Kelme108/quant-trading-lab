"""Tick recorder (b3/data/tick_recorder.py) on a fake MT5 module: windows split at the cap, no tick counted twice,
final vs partial days, final days never read again."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime, time

import numpy as np

from b3.data import tick_recorder as tr

DT = np.dtype([("time_msc", "i8"), ("bid", "f8"), ("ask", "f8"), ("last", "f8"), ("volume_real", "f8"), ("flags", "u4")])


class FakeMT5:
    COPY_TICKS_ALL = -1

    def __init__(self, ticks: np.ndarray, cap: int = 100_000):
        self.ticks, self.cap, self.calls = ticks, cap, 0

    def symbol_select(self, sym, on):
        return True

    def copy_ticks_range(self, sym, a, b, flags):
        self.calls += 1
        a_ms, b_ms = int(a.timestamp() * 1000), int(b.timestamp() * 1000)
        ms = self.ticks["time_msc"]
        sel = self.ticks[(ms >= a_ms) & (ms <= b_ms)]           # inclusive end, like the terminal
        return sel[: self.cap]


def _day_ticks(day: date, n: int, step_ms: int = 100, start=time(10, 0)) -> np.ndarray:
    t0 = tr._ms(day, start)
    t = np.zeros(n, DT)
    t["time_msc"] = t0 + np.arange(n) * step_ms
    t["last"] = 170000.0
    t["flags"] = np.where(np.arange(n) % 2 == 0, 1336, 1368)
    return t


def test_window_split_and_no_duplicates(tmp_path):
    day = date(2026, 11, 16)
    ticks = _day_ticks(day, 30_000, step_ms=10)            # 30k ticks in 5 minutes: one 20-minute window
    fake = FakeMT5(ticks, cap=8_000)
    tr.NEAR_CAP, old = 7_000, tr.NEAR_CAP
    try:
        parts = tr.read_day(fake, "WINZ26", day)
    finally:
        tr.NEAR_CAP = old
    got = np.concatenate(parts)["time_msc"]
    assert len(got) == len(ticks)
    assert np.array_equal(np.sort(got), ticks["time_msc"])


def test_boundary_tick_counted_once():
    day = date(2026, 11, 16)
    t = np.zeros(1, DT)
    t["time_msc"] = tr._ms(day, time(9, 10))                # exactly on a 20-minute window boundary
    t["flags"] = 1336
    parts = tr.read_day(FakeMT5(t), "WINZ26", day)
    assert sum(len(p) for p in parts) == 1


def test_final_and_partial_days(tmp_path, monkeypatch):
    day = date(2026, 11, 16)
    fake = FakeMT5(_day_ticks(day, 1_000))
    monkeypatch.setattr(tr, "symbols_for", lambda d, h: ["WINZ26"])
    during = datetime.combine(day, time(15, 0), tr.SP)
    out = tr.run(fake, day, day, during, out=tmp_path, log=lambda *_: None)
    assert out[0]["final"] is False and out[0]["rows"] == 1_000
    after = datetime.combine(day, time(19, 30), tr.SP)
    out = tr.run(fake, day, day, after, out=tmp_path, log=lambda *_: None)
    assert out[0]["final"] is True
    calls = fake.calls
    assert tr.run(fake, day, day, after, out=tmp_path, log=lambda *_: None) == []
    assert fake.calls == calls                               # a final day is never read again
    meta = json.loads((tmp_path / "WINZ26" / "2026-11-16.json").read_text())
    assert meta["buy_aggressor"] == 500 and meta["sell_aggressor"] == 500 and meta["trades"] == 1_000
    with gzip.open(tmp_path / "WINZ26" / "2026-11-16.csv.gz", "rt") as fh:
        assert fh.readline().strip() == ",".join(tr.FIELDS)
        assert sum(1 for _ in fh) == 1_000


def test_symbols_active_and_next():
    from b3.calendar import Holidays
    h = Holidays.from_file()
    assert tr.symbols_for(date(2026, 11, 16), h) == ["WINZ26", "WING27", "WDOZ26", "WDOF27"]
