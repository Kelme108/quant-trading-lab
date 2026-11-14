"""P-001..P-003 (b3/strategies/proxies.py) on SYNTHETIC session-only bars: causal, same decisions from the live
window as from the full history, and a hand-built opening-range day. Nothing here is market data."""

import random
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd
import pytest

from b3.backtest import BacktestConfig, run
from b3.checks import causality_problems, window_parity_problems
from b3.markets import market
from b3.strategies.proxies import RULES, OpeningRangeBreakout

UTC = timezone.utc


def synthetic_sessions(symbol, days=30, seed=3, start=5000.0, step=0.5, tf=5):
    m = market(symbol)
    rng = random.Random(seed)
    d, rows, prev = date(2026, 1, 5), [], start
    while len({r[0].date() for r in rows}) < days:
        if d.weekday() < 5:
            t = datetime.combine(d, m.open, m.zone)
            end = datetime.combine(d, m.close, m.zone)
            while t + timedelta(minutes=tf) <= end:
                o = prev + step * rng.randint(-3, 3)           # overnight / bar gaps
                c = o + step * rng.randint(-6, 6)
                rows.append((t, o, max(o, c) + step * rng.randint(0, 3), min(o, c) - step * rng.randint(0, 3), c,
                             float(rng.randint(50, 500))))
                prev, t = c, t + timedelta(minutes=tf)
        d += timedelta(days=1)
    return pd.DataFrame([(pd.Timestamp(r[0].astimezone(UTC)),) + r[1:] for r in rows],
                        columns=["time", "open", "high", "low", "close", "volume"])


@pytest.mark.parametrize("rule_id", sorted(RULES))
@pytest.mark.parametrize("symbol", ["US500", "EURUSD"])
def test_rules_are_causal_and_match_the_live_window(rule_id, symbol):
    step = 0.5 if symbol == "US500" else 0.0001
    start = 5000.0 if symbol == "US500" else 1.1
    tf = RULES[rule_id].timeframe_min
    frame = synthetic_sessions(symbol, step=step, start=start, tf=tf, days=45 if tf == 5 else 6)
    strategy = RULES[rule_id].on(symbol)()
    assert causality_problems(strategy, frame) == []
    assert window_parity_problems(strategy, frame, samples=60) == []


def test_rules_trade_on_synthetic_data_and_never_hold_overnight():
    for rule_id, rule in RULES.items():
        tf = rule.timeframe_min
        frame = synthetic_sessions("US500", days=45 if tf == 5 else 6, tf=tf)
        cfg = BacktestConfig(max_entries_per_day=1) if rule_id == "P-001" else BacktestConfig()
        r = run(frame, rule.on("US500")(), market("US500").cost("base"), cfg)
        assert r.trades, rule_id
        assert r.positions_held_overnight == 0, rule_id


def test_opening_range_breakout_long_with_the_range_low_as_stop():
    m = market("US500")
    d = date(2026, 1, 6)
    rows = []
    for day in (date(2026, 1, 2), date(2026, 1, 5)):     # two flat sessions first: the rule's warm-up is 120 bars
        t = datetime.combine(day, time(9, 30), m.zone)
        rows += [(pd.Timestamp((t + timedelta(minutes=5 * k)).astimezone(UTC)), 5000.0, 5001.0, 4999.0, 5000.0, 100.0)
                 for k in range(78)]
    t0 = datetime.combine(d, time(9, 30), m.zone)
    for k in range(78):
        if k < 6:                       # opening range 4990..5010
            o, h, lo, c = 5000.0, 5010.0, 4990.0, 5000.0
        elif k == 6:                    # first close above the range -> long at the open of bar 7
            o, h, lo, c = 5000.0, 5016.0, 4999.0, 5015.0
        else:
            o, h, lo, c = 5015.0, 5016.0, 5014.0, 5015.0
        rows.append((pd.Timestamp((t0 + timedelta(minutes=5 * k)).astimezone(UTC)), o, h, lo, c, 100.0))
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    r = run(frame, OpeningRangeBreakout.on("US500")(), m.cost("optimistic"), BacktestConfig(max_entries_per_day=1))
    (t,) = r.trades
    assert (t.side, t.stop_price, t.entry_price, t.entry_reason) == ("long", 4990.0, 5015.0, "orb_up")
    assert t.exit_reason == "end_of_day_flatten"
