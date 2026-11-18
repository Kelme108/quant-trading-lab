"""Strategy contract for B3 futures: one object for the backtester AND the live engine.

A strategy subclasses `B3Strategy` and implements two methods:

    indicators(df) -> df    vectorised and CAUSAL: row t may only use rows <= t (checked by
                            b3/checks.py with lab/causality.py). Add columns, never drop rows.
    decide(row, position) -> Signal
                            the decision after bar `row` has closed. `row` is a namedtuple with
                            the bar, the session features and the indicator columns. `position`
                            is None when flat; volume > 0 is long, volume < 0 is short.

The backtester calls `prepare()` once on the whole history and then `decide()` bar by bar; the live
engine calls `signal(bars, position)` with the last `warmup + 4` closed bars, which runs the same
two methods on that window. The two paths agree only if every indicator is fully determined by
`warmup` bars; b3/checks.py `window_parity` verifies it, so a too-short warm-up is caught before
any result is read.

Actions (live.core.models.Signal.action):
    "enter"        open a long position (the live engine already supports it)
    "enter_short"  open a short position: the backtester supports it; the live engine IGNORES it
                   (treated as "hold") until short selling is implemented and approved (plan F3)
    "exit"         close the open position at the next bar's open
    "hold"         do nothing
Every entry carries `stop_price`, on the tick grid, below the last close for a long and above it for
a short. The book is always flat at the session's `flatten_at` (calendar), whatever the strategy says.

Session features added before `indicators()` (all causal and known in advance):
    local_date      the session date in Sao Paulo (datetime.date)
    minute_of_day   minutes since local midnight at the bar's OPEN
    bar_in_day      0 for the first bar of the session, 1 for the next...
    day_open        open price of the session's first bar
    minutes_to_close  minutes from the bar's CLOSE to the session close (official table)
A strategy that uses them needs `warmup` to cover a full session plus its own lookback.
"""

from __future__ import annotations

import hashlib
import inspect
import math
from datetime import timedelta
from pathlib import Path

import pandas as pd

from b3.calendar import SP_TZ, B3SessionCalendar, SessionRules
from b3.instruments import Instrument, instrument_for
from live.core.models import Bar, Position, Signal

ENTER_LONG, ENTER_SHORT, EXIT, HOLD = "enter", "enter_short", "exit", "hold"
MOVE_STOP = "move_stop"   # tighten the server stop of the open position to Signal.stop_price (live engine only)
ACTIONS = frozenset({ENTER_LONG, ENTER_SHORT, EXIT, HOLD, MOVE_STOP})
BASE_COLUMNS = ("time", "open", "high", "low", "close", "volume")
SESSION_COLUMNS = ("local_date", "minute_of_day", "bar_in_day", "day_open", "minutes_to_close")


def bars_to_frame(bars: list[Bar]) -> pd.DataFrame:
    return pd.DataFrame({
        "time": pd.to_datetime([b.time for b in bars], utc=True),
        "open": [b.open for b in bars], "high": [b.high for b in bars], "low": [b.low for b in bars],
        "close": [b.close for b in bars], "volume": [b.volume for b in bars],
    })


def session_features(df: pd.DataFrame, calendar: B3SessionCalendar, timeframe_min: int) -> pd.DataFrame:
    out = df.copy()
    local = out["time"].dt.tz_convert(getattr(calendar, "tz", SP_TZ))   # SP_TZ for WIN/WDO; the market's zone for a proxy
    out["local_date"] = local.dt.date
    out["minute_of_day"] = local.dt.hour * 60 + local.dt.minute
    out["bar_in_day"] = out.groupby("local_date").cumcount()
    out["day_open"] = out.groupby("local_date")["open"].transform("first")
    closes = {}
    for d in out["local_date"].unique():
        s = calendar.session(d)
        closes[d] = s.close if s is not None else None
    bar_close = local + timedelta(minutes=timeframe_min)
    out["minutes_to_close"] = [
        (closes[d] - c).total_seconds() / 60.0 if closes[d] is not None else math.nan
        for d, c in zip(out["local_date"], bar_close)
    ]
    return out


def tick_floor(price: float, tick: float) -> float:
    return round(math.floor(price / tick + 1e-9) * tick, 10)


def tick_ceil(price: float, tick: float) -> float:
    return round(math.ceil(price / tick - 1e-9) * tick, 10)


class B3Strategy:
    name: str = ""
    root: str = ""                 # "WIN" or "WDO"
    timeframe_min: int = 5
    warmup: int = 1                # closed bars the decision needs
    rules: SessionRules = SessionRules()
    params: dict = {}

    def __init__(self, calendar: B3SessionCalendar | None = None) -> None:
        if not self.name or self.root not in ("WIN", "WDO"):
            raise ValueError(f"{type(self).__name__}: set `name` and `root` ('WIN' or 'WDO')")
        self.calendar = calendar or B3SessionCalendar(self.root, rules=self.rules)
        if self.calendar.rules != self.rules:
            raise ValueError("the calendar's session rules differ from the strategy's own rules")

    # ---- identity ----
    @property
    def hash(self) -> str:
        source = Path(inspect.getsourcefile(type(self))).read_bytes()
        ident = repr((self.name, self.root, self.timeframe_min, self.warmup, self.rules,
                      sorted(self.params.items()))).encode()
        return hashlib.sha256(source + ident).hexdigest()[:12]

    def instrument(self) -> Instrument:
        """Price grid and point value the backtester uses (a proxy market overrides it)."""
        return instrument_for(self.root)

    # ---- to override ----
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def decide(self, row, position: Position | None) -> Signal:
        return Signal(HOLD)

    # ---- shared paths ----
    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in BASE_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"frame lacks columns {missing}")
        out = self.indicators(session_features(df, self.calendar, self.timeframe_min))
        if len(out) != len(df):
            raise ValueError("indicators() must not add or drop rows")
        return out

    def signal(self, bars: list[Bar], position: Position | None) -> Signal:
        """The live engine's entry point (live.core.engine.Strategy protocol)."""
        frame = self.prepare(bars_to_frame(bars))
        row = next(frame.tail(1).itertuples(index=False, name="Row"))
        sig = self.decide(row, position)
        if sig.action not in ACTIONS:
            raise ValueError(f"unknown action {sig.action!r}")
        return sig
