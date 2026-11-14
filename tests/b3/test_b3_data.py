"""Data layer: MT5 depth/download with a fake terminal, conversion of server times, checks and the
back-adjusted continuous series."""

import gzip
import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd
import pytest

from b3.calendar import Holidays
from b3.contracts import roll_schedule
from b3.data import mt5_history
from b3.data.continuous import back_adjust
from b3.data.quality import check_bars
from b3.data.store import load_rates, read_manifest, server_to_utc
from b3_helpers import calendar, frame_from_closes, random_walk_frame, session_times

UTC = timezone.utc


class FakeTerminal:
    """Just enough of the MetaTrader5 module for b3/data/mt5_history.py. Server clock = Sao Paulo."""

    TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_M30 = 1, 5, 15, 30
    TIMEFRAME_H1, TIMEFRAME_D1 = 16385, 16408
    COPY_TICKS_ALL, TICK_FLAG_BUY, TICK_FLAG_SELL = -1, 32, 64

    def __init__(self, frame: pd.DataFrame):
        local = frame["time"].dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
        self.server_epochs = ((local - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)).tolist()
        self.frame = frame.reset_index(drop=True)
        self.calls = []

    def initialize(self, **kw):
        self.init_kw = kw
        return True

    def shutdown(self):
        pass

    def account_info(self):
        return SimpleNamespace(company="Corretora Teste", server="TESTE-DEMO", trade_mode=0, margin_mode=0,
                               currency="BRL", login=123, password="never")

    def terminal_info(self):
        return SimpleNamespace(build=5000)

    def symbols_get(self, pattern):
        names = ["WIN$N", "WINZ26", "WDOZ26"]
        return [SimpleNamespace(name=n) for n in names if n.startswith(pattern.rstrip("*"))]

    def symbol_select(self, symbol, enable):
        return symbol in ("WIN$N", "WINZ26", "WDOZ26")

    def copy_rates_range(self, symbol, tf, start, end):
        self.calls.append((symbol, tf, start, end))
        out = []
        for e, r in zip(self.server_epochs, self.frame.itertuples(index=False)):
            if start.timestamp() <= e < end.timestamp():        # MT5 compares on the server clock
                out.append({"time": e, "open": r.open, "high": r.high, "low": r.low, "close": r.close,
                            "tick_volume": 10, "spread": 1, "real_volume": int(r.volume)})
        return out

    def copy_ticks_from(self, symbol, start, count, flags):
        base = self.server_epochs[0] * 1000
        return [{"time_msc": base + i, "bid": 1.0, "ask": 2.0, "last": 1.5, "volume_real": 1.0,
                 "flags": 32 if i % 2 else 2} for i in range(min(count, 10))]

    def copy_ticks_range(self, symbol, start, end, flags):
        return self.copy_ticks_from(symbol, start, 3, flags)


def test_depth_report_never_contains_credentials():
    term = FakeTerminal(random_walk_frame(seed=1))
    rep = mt5_history.depth_report(term, ["WIN$N", "PETR4"], ["M5"], first_year=2025,
                                   now=lambda: datetime(2026, 11, 13, tzinfo=UTC))
    bars = {b["symbol"]: b for b in rep["bars"]}
    assert bars["WIN$N"]["bars"] == len(term.frame) and bars["WIN$N"]["bars_per_year"] == {2026: len(term.frame)}
    assert bars["PETR4"]["error"] == "symbol not available"
    assert rep["ticks"][0]["recent_with_aggressor_flag"] == 5
    text = json.dumps(rep)
    assert "never" not in text and "123" not in json.dumps(rep["account"])


def test_download_round_trip_keeps_server_time_and_converts_with_the_stated_zone(tmp_path):
    frame = random_walk_frame(seed=1)
    term = FakeTerminal(frame)
    m = mt5_history.download_rates(term, "WIN$N", "M5", datetime(2026, 11, 1, tzinfo=UTC),
                                   datetime(2026, 11, 14, tzinfo=UTC), tmp_path)
    path = tmp_path / m["file"]
    assert m["file"] == "WIN_S_N-M5.csv.gz" and m["rows"] == len(frame)
    with gzip.open(path, "rt") as f:
        assert f.readline().strip().startswith("time_server,open")
    assert read_manifest(path)["sha256"] == m["sha256"]
    loaded = load_rates(path, server_tz="America/Sao_Paulo")
    assert loaded["time"].tolist() == frame["time"].tolist()
    assert loaded["volume"].tolist() == frame["volume"].tolist()
    fixed = load_rates(path, server_tz=None, server_utc_offset_hours=-3)
    assert fixed["time"].tolist() == frame["time"].tolist()          # no DST in 2026


def test_server_time_conversion_follows_brazil_dst():
    wall = pd.Series([int(datetime(2018, 1, 10, 10, 0).replace(tzinfo=UTC).timestamp())])
    assert server_to_utc(wall, "America/Sao_Paulo").iloc[0].hour == 12     # UTC-2 in Brazilian summer 2018
    with pytest.raises(ValueError):
        server_to_utc(wall, "America/Sao_Paulo", -3)


def test_ticks_download(tmp_path):
    term = FakeTerminal(random_walk_frame(seed=1))
    m = mt5_history.download_ticks(term, "WINZ26", datetime(2026, 11, 9, tzinfo=UTC),
                                   datetime(2026, 11, 11, tzinfo=UTC), tmp_path)
    assert m["rows"] == 6 and (tmp_path / m["file"]).exists()


def test_cli_symbols_command(capsys, tmp_path):
    term = FakeTerminal(random_walk_frame(seed=1))
    assert mt5_history.main(["symbols", "--env", str(tmp_path / "none.env")], mt5_module=term) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["symbols"]["WIN*"] == ["WIN$N", "WINZ26"]


def test_quality_flags_defects():
    f = random_walk_frame(seed=1)
    clean = check_bars(f, 5, calendar())
    assert clean["ohlc_inconsistent"] == 0 and clean["missing_slots_inside_session"] == 0
    assert clean["bars_outside_session"] == 0 and clean["first_bar_local_time"] == {"09:00": 5}
    bad = f.drop(index=[30, 31]).copy()
    bad.loc[40, "high"] = bad.loc[40, "low"] - 5
    bad.loc[50, "volume"] = 0
    bad.loc[60, ["open", "high", "low", "close"]] = bad.loc[60, "close"] * 1.05
    rep = check_bars(bad.reset_index(drop=True), 5, calendar())
    assert rep["missing_slots_inside_session"] == 2 and rep["ohlc_inconsistent"] >= 1
    assert rep["zero_volume"] == 1 and rep["jumps"]
    holiday = frame_from_closes([172_000.0] * 5, [date(2026, 11, 20)])
    assert check_bars(holiday, 5, calendar())["bars_on_official_holidays"] == ["2026-11-20"]


def test_back_adjust_removes_the_roll_jump_and_keeps_the_last_contract_raw():
    h = Holidays.from_file()
    days = h.trading_days(date(2026, 10, 5), date(2026, 10, 16))
    old = frame_from_closes([170_000.0 + 5 * (i % 7) for i in range(113 * len(days))], days, start=170_000.0)
    new = old.copy()
    for c in ("open", "high", "low", "close"):
        new[c] = new[c] + 1_500.0                        # the next contract trades 1,500 points higher
    sched = roll_schedule("WIN", days[0], days[-1], h)
    assert [s.contract.code for s in sched] == ["WINV26", "WINZ26"]
    series, rolls = back_adjust({"WINV26": old, "WINZ26": new}, sched)
    assert rolls[0]["diff"] == pytest.approx(1_500.0)
    assert series["time"].is_monotonic_increasing and not series["time"].duplicated().any()
    last_day = series[series["contract"] == "WINZ26"]
    assert (last_day["adj_offset"] == 0).all()
    first = series[series["contract"] == "WINV26"]
    raw_first = old[old["time"].isin(first["time"])]
    assert (first["close"].to_numpy() - raw_first["close"].to_numpy() == 1_500.0).all()
    with pytest.raises(KeyError):
        back_adjust({"WINV26": old}, sched)
