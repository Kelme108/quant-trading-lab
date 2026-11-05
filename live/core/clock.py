"""Injectable clock and trading calendars (B3 futures session, 24/7 crypto)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Protocol

UTC = timezone.utc
BRT = timezone(timedelta(hours=-3))  # Brazil has had no DST since 2019


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FakeClock:
    def __init__(self, start: datetime) -> None:
        assert start.tzinfo is not None
        self._now = start

    def now(self) -> datetime:
        return self._now

    def set(self, t: datetime) -> None:
        assert t.tzinfo is not None
        self._now = t

    def advance(self, **kw) -> None:
        self._now += timedelta(**kw)


@dataclass(frozen=True)
class SessionConfig:
    """Local (BRT) times. Defaults are placeholders: confirm against the
    broker's real session for WIN/WDO before use (see live/DECISIONS.md)."""

    open: time = time(9, 0)
    entry_start: time = time(9, 15)   # no entries in the opening noise
    entry_end: time = time(17, 0)
    flatten_at: time = time(17, 45)   # close everything from here on
    close: time = time(18, 0)
    holidays: frozenset = field(default_factory=frozenset)  # of datetime.date


class B3Calendar:
    """Phases: closed | no_entry | entry | flatten."""

    def __init__(self, cfg: SessionConfig | None = None, tz=BRT) -> None:
        self.cfg, self.tz = cfg or SessionConfig(), tz

    def local(self, dt: datetime) -> datetime:
        return dt.astimezone(self.tz)

    def is_trading_day(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self.cfg.holidays

    def phase(self, dt: datetime) -> str:
        loc = self.local(dt)
        t, c = loc.time(), self.cfg
        if not self.is_trading_day(loc.date()) or t < c.open or t >= c.close:
            return "closed"
        if t >= c.flatten_at:
            return "flatten"
        if c.entry_start <= t < c.entry_end:
            return "entry"
        return "no_entry"

    def day_key(self, dt: datetime) -> str:
        return self.local(dt).date().isoformat()

    def week_key(self, dt: datetime) -> str:
        return self.week_start_utc(dt).astimezone(self.tz).date().isoformat()

    def day_start_utc(self, dt: datetime) -> datetime:
        loc = self.local(dt)
        return datetime.combine(loc.date(), time.min, self.tz).astimezone(UTC)

    def week_start_utc(self, dt: datetime) -> datetime:
        loc = self.local(dt)
        monday = loc.date() - timedelta(days=loc.weekday())
        return datetime.combine(monday, time.min, self.tz).astimezone(UTC)


class AlwaysOpenCalendar(B3Calendar):
    """24/7 markets (crypto): always `entry`; days and weeks in UTC."""

    def __init__(self) -> None:
        super().__init__(SessionConfig(), UTC)

    def phase(self, dt: datetime) -> str:
        return "entry"
