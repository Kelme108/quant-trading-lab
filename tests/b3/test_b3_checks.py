from pathlib import Path

import pandas as pd

from b3.calendar import SessionRules
from b3.checks import causality_problems, window_parity_problems
from b3.strategy import ENTER_LONG, HOLD, B3Strategy
from b3.strategy_check import check_b3_strategy_source
from b3_helpers import ChannelBreakout, random_walk_frame
from live.core.models import Signal


class PeeksAhead(ChannelBreakout):
    name = "test_peek"

    def indicators(self, df):
        df = super().indicators(df)
        df["next_close"] = df["close"].shift(-1)          # the future
        return df


class ShortWarmup(B3Strategy):
    """Uses a 50-bar mean but declares a 10-bar warm-up: the live window cannot reproduce it."""

    name, root, timeframe_min, warmup = "test_short_warmup", "WIN", 5, 10
    rules = SessionRules(15, 30, 10)

    def indicators(self, df):
        df["m50"] = df["close"].rolling(50, min_periods=1).mean()
        return df

    def decide(self, row, position):
        if position is None and row.close > row.m50:
            return Signal(ENTER_LONG, stop_price=row.close - 100.0)
        return Signal(HOLD)


def test_good_strategy_passes_both_checks():
    f = random_walk_frame(seed=2)
    assert causality_problems(ChannelBreakout(), f) == []
    assert window_parity_problems(ChannelBreakout(), f, samples=60) == []


def test_lookahead_is_caught():
    problems = causality_problems(PeeksAhead(), random_walk_frame(seed=2))
    assert problems and any("prefix" in p or "corruption" in p for p in problems)


def test_too_short_warmup_is_caught():
    assert window_parity_problems(ShortWarmup(), random_walk_frame(seed=2), samples=60)


def test_session_features_are_causal():
    class SessionUser(ChannelBreakout):
        name, warmup = "test_session_user", 130

        def decide(self, row, position):
            if position is None and row.bar_in_day == 20 and row.close > row.day_open:
                return Signal(ENTER_LONG, stop_price=row.close - 100.0)
            return Signal(HOLD)

    f = random_walk_frame(seed=4)
    assert causality_problems(SessionUser(), f) == []
    assert window_parity_problems(SessionUser(), f, samples=40) == []
    prepared = SessionUser().prepare(f)
    first = prepared.groupby("local_date").head(1)
    assert (first["bar_in_day"] == 0).all() and (first["day_open"] == first["open"]).all()
    assert prepared["minutes_to_close"].iloc[0] == 18 * 60 + 25 - (9 * 60 + 5)


GOOD = '''
from b3.calendar import SessionRules
from b3.strategy import B3Strategy, HOLD
from live.core.models import Signal


class SessionMomentum_B001_v1(B3Strategy):
    name = "session_momentum"
    root = "WIN"
    timeframe_min = 5
    warmup = 200
    rules = SessionRules(15, 30, 10)

    def indicators(self, df):
        df["r"] = df["close"].pct_change().rolling(12).sum()
        return df

    def decide(self, row, position):
        return Signal(HOLD)
'''


def test_static_check_accepts_a_proper_file_and_rejects_violations(tmp_path: Path):
    good = tmp_path / "SessionMomentum_B001_v1.py"
    good.write_text(GOOD, encoding="utf-8")
    assert check_b3_strategy_source(good, "B-001") == []

    bad = tmp_path / "SessionMomentum_B002_v1.py"
    bad.write_text(GOOD.replace("SessionMomentum_B001_v1", "SessionMomentum_B002_v1")
                   .replace('df["close"].pct_change()', 'df["close"].shift(-1)')
                   .replace("import B3Strategy, HOLD", "import B3Strategy, HOLD\nimport requests")
                   .replace('rolling(12)', 'rolling(12, center=True)')
                   .replace('warmup = 200', 'warmup = 0'), encoding="utf-8")
    problems = " | ".join(check_b3_strategy_source(bad, "B-001"))
    for needle in ("says B-002", "requests", "negative period", "centered", "warmup"):
        assert needle in problems, needle
