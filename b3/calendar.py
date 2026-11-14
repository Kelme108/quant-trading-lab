"""B3 trading calendar: official holidays, session hours by date, and the engine's session phases.

Local time is America/Sao_Paulo (not a fixed UTC-3): Brazil had daylight saving time until
February 2019, and the backtest history may start before that.

Three layers:
- `Holidays`: which days have a session. Only years transcribed from a B3 Oficio Circular
  (b3/config/holidays.json) or explicitly inferred from data are known; asking about any other
  year raises `UnknownCalendarYear` instead of guessing.
- `SessionTable`: regular open and close per root and date range (b3/config/sessions.json).
- `SessionRules` + `B3SessionCalendar`: where a strategy may enter and when everything is closed,
  as offsets from the day's open and close. `B3SessionCalendar` is a drop-in for
  live.core.clock.B3Calendar, so the backtester and the live engine share one definition.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from live.core.clock import B3Calendar, SessionConfig

SP_TZ = ZoneInfo("America/Sao_Paulo")
CONFIG_DIR = Path(__file__).parent / "config"
HOLIDAYS_PATH = CONFIG_DIR / "holidays.json"
SESSIONS_PATH = CONFIG_DIR / "sessions.json"


class UnknownCalendarYear(LookupError):
    """The calendar has no official (or inferred) holiday list for this year."""


class UnknownSession(LookupError):
    """No session period in the table covers this root and date."""


def _d(text: str) -> date:
    return date.fromisoformat(text)


def _t(text: str) -> time:
    return time.fromisoformat(text)


# ---------------------------------------------------------------------------------------------
# Holidays
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Holidays:
    closed: frozenset = frozenset()                       # dates with no session
    special_open: tuple = ()                              # ((date, time), ...) late opens
    known_years: frozenset = frozenset()
    sources: tuple = ()                                   # (year, source text), for the record

    @classmethod
    def from_file(cls, path: str | Path = HOLIDAYS_PATH) -> "Holidays":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        closed, special, years, sources = set(), [], set(), []
        for year, block in raw["years"].items():
            years.add(int(year))
            sources.append((int(year), block.get("source", "")))
            for day in block.get("closed", {}):
                d = _d(day)
                if d.year != int(year):
                    raise ValueError(f"holidays.json: {day} listed under year {year}")
                closed.add(d)
            for day, info in block.get("special", {}).items():
                if "open" in info:
                    special.append((_d(day), _t(info["open"])))
        return cls(frozenset(closed), tuple(sorted(special)), frozenset(years), tuple(sources))

    def with_inferred(self, closed: Iterable[date], years: Iterable[int], source: str) -> "Holidays":
        """Add closures inferred from data (weekdays without bars) for years the file does not cover.

        Inferring is acceptable for HISTORY because exchange holidays are announced in advance, so a
        rule could have known them; it must never be used for future dates."""
        years = {int(y) for y in years}
        overlap = years & self.known_years
        if overlap:
            raise ValueError(f"years {sorted(overlap)} already have an official list; do not infer them")
        closed = {d for d in closed if d.year in years}
        return Holidays(self.closed | frozenset(closed), self.special_open,
                        self.known_years | frozenset(years),
                        self.sources + tuple((y, source) for y in sorted(years)))

    def _check_year(self, d: date) -> None:
        if d.year not in self.known_years:
            raise UnknownCalendarYear(
                f"no B3 holiday list for {d.year}; add it from the B3 Oficio Circular or infer it from data")

    def is_trading_day(self, d: date) -> bool:
        if d.weekday() >= 5:
            return False
        self._check_year(d)
        return d not in self.closed

    def special_open_time(self, d: date) -> time | None:
        return next((t for day, t in self.special_open if day == d), None)

    def add_trading_days(self, d: date, n: int) -> date:
        """The n-th trading day after (n > 0) or before (n < 0) d. n = 0 returns d itself."""
        step = 1 if n >= 0 else -1
        left, cur = abs(n), d
        while left:
            cur += timedelta(days=step)
            if self.is_trading_day(cur):
                left -= 1
        return cur

    def next_trading_day(self, d: date, include_today: bool = False) -> date:
        if include_today and self.is_trading_day(d):
            return d
        return self.add_trading_days(d, 1)

    def trading_days(self, start: date, end: date) -> list[date]:
        """Trading days in [start, end]."""
        out, cur = [], start
        while cur <= end:
            if self.is_trading_day(cur):
                out.append(cur)
            cur += timedelta(days=1)
        return out


def infer_closed_weekdays(days_with_bars: Iterable[date], start: date, end: date) -> list[date]:
    """Weekdays in [start, end] with no bar at all: holidays OR data gaps (b3/data/quality.py
    separates the two by checking the reference series and the second contract)."""
    have = set(days_with_bars)
    out, cur = [], start
    while cur <= end:
        if cur.weekday() < 5 and cur not in have:
            out.append(cur)
        cur += timedelta(days=1)
    return out


# ---------------------------------------------------------------------------------------------
# Session hours
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class SessionPeriod:
    root: str
    start: date
    end: date | None          # inclusive; None = open-ended
    open: time
    close: time
    preopen_minutes: int = 5
    expiry_close: time | None = None   # the expiring contract stops earlier on its expiry day
    source: str = ""

    def covers(self, root: str, d: date) -> bool:
        return root == self.root and self.start <= d and (self.end is None or d <= self.end)


@dataclass(frozen=True)
class SessionTable:
    periods: tuple = ()

    @classmethod
    def from_file(cls, path: str | Path = SESSIONS_PATH) -> "SessionTable":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("timezone") != "America/Sao_Paulo":
            raise ValueError("sessions.json must be in America/Sao_Paulo local time")
        periods = []
        for p in raw["periods"]:
            periods.append(SessionPeriod(
                root=p["root"], start=_d(p["start"]), end=_d(p["end"]) if p.get("end") else None,
                open=_t(p["open"]), close=_t(p["close"]), preopen_minutes=int(p.get("preopen_minutes", 5)),
                expiry_close=_t(p["expiry_day_close_of_expiring_contract"])
                if p.get("expiry_day_close_of_expiring_contract") else None,
                source=p.get("source", "")))
        return cls(tuple(periods)).validated()

    def validated(self) -> "SessionTable":
        by_root: dict[str, list[SessionPeriod]] = {}
        for p in self.periods:
            if p.open >= p.close:
                raise ValueError(f"{p.root} {p.start}: open {p.open} not before close {p.close}")
            by_root.setdefault(p.root, []).append(p)
        for root, ps in by_root.items():
            ps.sort(key=lambda p: p.start)
            for a, b in zip(ps, ps[1:]):
                if a.end is None or a.end >= b.start:
                    raise ValueError(f"{root}: session periods starting {a.start} and {b.start} overlap")
        return self

    def with_periods(self, extra: Iterable[SessionPeriod]) -> "SessionTable":
        return SessionTable(self.periods + tuple(extra)).validated()

    def period(self, root: str, d: date) -> SessionPeriod:
        for p in self.periods:
            if p.covers(root, d):
                return p
        raise UnknownSession(f"no session hours for {root} on {d}; see b3/config/sessions.json")


def infer_session_table(bar_open_times_utc: Iterable[datetime], root: str, timeframe_min: int,
                        source: str) -> list[SessionPeriod]:
    """Propose session periods from downloaded bars: per calendar month, the most common first-bar
    open time and last-bar close time (local). Consecutive months with equal hours are merged.

    The result is a PROPOSAL for a human to check against the B3 circular of each period; it is
    never written to sessions.json automatically."""
    tf = timedelta(minutes=timeframe_min)
    days: dict[date, list[datetime]] = {}
    for t in bar_open_times_utc:
        loc = t.astimezone(SP_TZ)
        days.setdefault(loc.date(), []).append(loc)
    months: dict[tuple[int, int], tuple[Counter, Counter, list[date]]] = {}
    for d, ts in sorted(days.items()):
        first, last = min(ts), max(ts)
        opens, closes, ds = months.setdefault((d.year, d.month), (Counter(), Counter(), []))
        opens[first.time()] += 1
        closes[(last + tf).time()] += 1
        ds.append(d)
    periods: list[SessionPeriod] = []
    for (_, _), (opens, closes, ds) in sorted(months.items()):
        o, c = opens.most_common(1)[0][0], closes.most_common(1)[0][0]
        if periods and periods[-1].open == o and periods[-1].close == c:
            last = periods[-1]
            periods[-1] = SessionPeriod(root, last.start, max(ds), o, c, source=source)
        else:
            periods.append(SessionPeriod(root, min(ds), max(ds), o, c, source=source))
    return periods


# ---------------------------------------------------------------------------------------------
# Phases for the engine and the backtester
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class SessionRules:
    """Where entries are allowed and when the book is flattened, relative to the day's session.

    Defaults are conservative placeholders; every strategy states its own rules ex ante."""

    entry_start_after_open_min: int = 15
    entry_end_before_close_min: int = 30
    flatten_before_close_min: int = 10

    def __post_init__(self) -> None:
        if min(self.entry_start_after_open_min, self.entry_end_before_close_min,
               self.flatten_before_close_min) < 0:
            raise ValueError("session rule offsets cannot be negative")
        if self.flatten_before_close_min > self.entry_end_before_close_min:
            raise ValueError("flatten must not come before the end of the entry window")


@dataclass(frozen=True)
class SessionDay:
    day: date
    open: datetime            # all local (America/Sao_Paulo), timezone-aware
    entry_start: datetime
    entry_end: datetime
    flatten_at: datetime
    close: datetime


class B3SessionCalendar(B3Calendar):
    """live.core.clock.B3Calendar with official holidays, dated session hours and DST-aware local time.

    Phases (same meaning as the parent): closed | no_entry | entry | flatten."""

    def __init__(self, root: str, holidays: Holidays | None = None, sessions: SessionTable | None = None,
                 rules: SessionRules | None = None) -> None:
        super().__init__(SessionConfig(), SP_TZ)
        self.root = root.upper()
        self.holidays = holidays or Holidays.from_file()
        self.sessions = sessions or SessionTable.from_file()
        self.rules = rules or SessionRules()
        self._cache: dict[date, SessionDay | None] = {}

    def is_trading_day(self, d: date) -> bool:
        return self.holidays.is_trading_day(d)

    def session(self, d: date) -> SessionDay | None:
        if d in self._cache:
            return self._cache[d]
        out = None
        if self.is_trading_day(d):
            p = self.sessions.period(self.root, d)
            opening = self.holidays.special_open_time(d) or p.open
            o = datetime.combine(d, opening, SP_TZ)
            c = datetime.combine(d, p.close, SP_TZ)
            r = self.rules
            entry_start = o + timedelta(minutes=r.entry_start_after_open_min)
            entry_end = c - timedelta(minutes=r.entry_end_before_close_min)
            flatten = c - timedelta(minutes=r.flatten_before_close_min)
            if not (o <= entry_start <= entry_end <= flatten <= c):
                raise ValueError(f"{self.root} {d}: session rules do not fit the session {opening}-{p.close}")
            out = SessionDay(d, o, entry_start, entry_end, flatten, c)
        self._cache[d] = out
        return out

    def phase(self, dt: datetime) -> str:
        loc = dt.astimezone(SP_TZ)
        s = self.session(loc.date())
        if s is None or loc < s.open or loc >= s.close:
            return "closed"
        if loc >= s.flatten_at:
            return "flatten"
        if s.entry_start <= loc < s.entry_end:
            return "entry"
        return "no_entry"
