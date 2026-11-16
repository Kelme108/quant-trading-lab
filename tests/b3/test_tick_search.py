"""Tick program (b3/tick_search.py): bars from ticks keep the aggressor volumes, the splits are enforced, and the
signals never look ahead."""

from __future__ import annotations

import gzip
from datetime import date

import numpy as np
import pytest

from b3 import tick_search as ts


def test_preregistration_and_locked_final_test():
    cfg = ts.load_config()
    assert cfg["approved_by_owner"] is True
    from b3 import pattern_search as ps
    assert len(ps.signal_settings({"families": cfg["families"]})) * 2 * 6 == 384
    with pytest.raises(PermissionError):
        ts.split_days(cfg, "final_test")
    assert ts.split_days(cfg, "exploration")[1] == date(2026, 12, 31)


def test_build_bars_from_fake_ticks(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "TICKS", tmp_path)
    d = date(2026, 11, 16)
    (tmp_path / "WINZ26").mkdir()
    base = 1794819600000 // 60_000 * 60_000              # a minute boundary on the server clock
    rows = ["time_msc,bid,ask,last,volume_real,flags",
            f"{base},0,0,170000,2,1336",                 # buy aggressor
            f"{base + 1000},0,0,170005,3,1368",          # sell aggressor
            f"{base + 2000},170000,170005,0,0,6",        # quote only: not a trade
            f"{base + 61_000},0,0,169995,1,1336"]
    with gzip.open(tmp_path / "WINZ26" / f"{d}.csv.gz", "wt") as fh:
        fh.write("\n".join(rows) + "\n")
    b = ts.build_bars("WIN", d, d, log=lambda *_: None)
    assert len(b) == 2
    first = b.iloc[0]
    assert (first.open, first.high, first.low, first.close) == (170000, 170005, 170000, 170005)
    assert (first.buy_vol, first.sell_vol, first.volume, first.n_trades) == (2, 3, 5, 2)
    # the server clock is B3 time: real UTC is 3 hours later
    assert b["time"].iloc[0].value // 10**6 == base + 3 * 3600 * 1000
    assert np.isinf(first.big_threshold)                 # fewer than 5 earlier sessions: no 'big' trades yet


def test_tick_signals_are_causal():
    if not ts.bars_path("WIN").exists():
        pytest.skip("no tick bars on this machine")
    cfg = ts.load_config()
    from b3 import pattern_search as ps
    short = ts.load_tick_frame("WIN", 1, date(2026, 11, 6), cfg)
    long = ts.load_tick_frame("WIN", 1, date(2026, 11, 16), cfg)
    n = len(short.df)
    assert (long.df["time"].iloc[:n].to_numpy() == short.df["time"].to_numpy()).all()
    s1, s2 = ts.TickSignals(short), ts.TickSignals(long)
    for fam, p in ps.signal_settings({"families": cfg["families"]}):
        assert (s1.direction(fam, p) == s2.direction(fam, p)[:n]).all(), fam
