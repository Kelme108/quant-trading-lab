"""Proxy markets (b3/markets.py): costs as a share of notional, New York session calendar, server-time
conversion, and the shared backtester on a synthetic US500 day. Nothing here is market data."""

from datetime import date, datetime, time, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from b3.backtest import run
from b3.calendar import SessionRules
from b3.markets import (MARKETS, NEW_YORK, ProxySessionCalendar, ProxyStrategy, infer_closed_days, load_bars,
                        market, server_to_utc)
from b3.strategy import ENTER_LONG, ENTER_SHORT, EXIT, HOLD
from live.core.models import Signal

UTC = timezone.utc
DAY = date(2026, 1, 6)          # a Tuesday in New York winter time (UTC-5)
SUMMER = date(2026, 7, 7)       # a Tuesday in New York summer time (UTC-4)
PRICE = 5000.0


def ny_day_frame(d=DAY, closes=None, tf=5, start=PRICE):
    """5-minute bars 09:30-16:00 New York (78 bars), opens at the previous close."""
    t = datetime.combine(d, time(9, 30), NEW_YORK)
    times = [pd.Timestamp((t + timedelta(minutes=tf * k)).astimezone(UTC)) for k in range(78)]
    closes = closes or [start] * 78
    rows, prev = [], start
    for ts, c in zip(times, closes):
        rows.append((ts, prev, max(prev, c) + 0.25, min(prev, c) - 0.25, c, 100.0))
        prev = c
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])


class Scripted(ProxyStrategy):
    name, symbol, timeframe_min, warmup = "scripted_us500", "US500", 5, 1
    rules = SessionRules(15, 30, 10)

    def __init__(self, script):
        super().__init__()
        self.script = script

    def decide(self, row, position):
        action, offset = self.script.get(row.bar_in_day, (HOLD, None))
        if action in (ENTER_LONG, ENTER_SHORT):
            return Signal(action, stop_price=round(row.close + offset, 2), reason=f"bar{row.bar_in_day}")
        return Signal(action, reason=f"bar{row.bar_in_day}")


def test_every_market_has_the_four_scenarios_scaled_from_base():
    for m in MARKETS.values():
        base = m.cost("base").notional_frac_per_side
        assert base == pytest.approx(m.base_round_trip / 2)
        assert m.cost("optimistic").notional_frac_per_side == pytest.approx(base / 2)
        assert m.cost("conservative").notional_frac_per_side == pytest.approx(base * 2)
        assert m.cost("stress").notional_frac_per_side == pytest.approx(base * 4)
    with pytest.raises(ValueError):
        market("IBOV")


def test_cash_cost_is_a_share_of_the_fill_notional():
    m = market("US500")
    c = m.cost("base")                      # 0.01% round trip -> 0.005% per side
    assert c.cash_cost(m.instrument(), 5000.0, 2.0) == pytest.approx(2 * 5000.0 * 0.00005)


def test_server_time_is_new_york_plus_seven_hours_in_winter_and_summer():
    # 16:30 server = 09:30 New York = 14:30 UTC in January and 13:30 UTC in July
    winter = int(datetime(2026, 1, 6, 16, 30, tzinfo=UTC).timestamp())
    summer = int(datetime(2026, 7, 7, 16, 30, tzinfo=UTC).timestamp())
    got = server_to_utc(pd.Series([winter, summer]))
    assert got.iloc[0] == pd.Timestamp("2026-01-06 14:30", tz="UTC")
    assert got.iloc[1] == pd.Timestamp("2026-07-07 13:30", tz="UTC")


def test_load_bars_reads_the_numpy_export(tmp_path):
    dt = np.dtype([("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                   ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])
    t0 = int(datetime(2026, 1, 6, 16, 30, tzinfo=UTC).timestamp())
    arr = np.array([(t0 + 300, 2, 3, 1, 2, 5, 1, 0), (t0, 1, 2, 0.5, 1.5, 4, 1, 0)], dtype=dt)   # out of order
    np.save(tmp_path / "US500-5m.npy", arr)
    f = load_bars("US500", "5m", tmp_path)
    assert list(f.columns) == ["time", "open", "high", "low", "close", "volume", "spread"]
    assert f["time"].tolist() == [pd.Timestamp("2026-01-06 14:30", tz="UTC"), pd.Timestamp("2026-01-06 14:35", tz="UTC")]


def test_calendar_phases_follow_the_new_york_session_through_dst():
    cal = ProxySessionCalendar(market("US500"), SessionRules(15, 30, 10))
    for d in (DAY, SUMMER):
        def at(h, mi):
            return datetime.combine(d, time(h, mi), NEW_YORK).astimezone(UTC)
        assert cal.phase(at(9, 29)) == "closed"
        assert cal.phase(at(9, 30)) == "no_entry"
        assert cal.phase(at(9, 45)) == "entry"
        assert cal.phase(at(15, 29)) == "entry"
        assert cal.phase(at(15, 30)) == "no_entry"
        assert cal.phase(at(15, 50)) == "flatten"
        assert cal.phase(at(16, 0)) == "closed"
    assert ProxySessionCalendar(market("US500"), closed_days=frozenset({DAY})).phase(
        datetime.combine(DAY, time(10, 0), NEW_YORK)) == "closed"


def test_session_features_are_in_the_market_time_zone():
    f = Scripted({}).prepare(ny_day_frame())
    assert f["bar_in_day"].iloc[0] == 0 and f["minute_of_day"].iloc[0] == 9 * 60 + 30
    assert f["minutes_to_close"].iloc[-1] == 0.0


def test_long_and_short_on_us500_with_notional_costs_and_flatten():
    closes = [PRICE] * 78
    for k in range(5, 78):
        closes[k] = PRICE + 10.0
    f = ny_day_frame(closes=closes)
    m = market("US500")
    cost = m.cost("base")
    # long decided after bar 3 (fills at bar 4 open = PRICE), exit after bar 5 (fills at bar 6 open = PRICE + 10)
    r = run(f, Scripted({3: (ENTER_LONG, -20.0), 5: (EXIT, None)}), cost)
    (t,) = r.trades
    assert (t.side, t.entry_price, t.exit_price) == ("long", PRICE, PRICE + 10.0)
    fee = 0.00005 * PRICE + 0.00005 * (PRICE + 10.0)
    assert t.cost_brl == pytest.approx(fee)
    assert t.net_brl == pytest.approx(10.0 - fee)
    # a short held to the end of the day is flattened at 15:50 New York
    r = run(f, Scripted({10: (ENTER_SHORT, 20.0)}), cost)
    (t,) = r.trades
    assert t.side == "short" and t.exit_reason == "end_of_day_flatten"
    assert t.exit_time.tz_convert(NEW_YORK).time() == time(15, 50)


def test_infer_closed_days_finds_weekdays_without_session_bars():
    a = ny_day_frame(DAY)
    b = ny_day_frame(DAY + timedelta(days=2))        # Thursday; Wednesday is missing
    closed = infer_closed_days(pd.concat([a, b], ignore_index=True), market("US500"))
    assert closed == frozenset({DAY + timedelta(days=1)})


def test_proxy_strategy_requires_a_known_symbol():
    class Bad(ProxyStrategy):
        name, symbol = "bad", "IBOV"
    with pytest.raises(ValueError):
        Bad()
