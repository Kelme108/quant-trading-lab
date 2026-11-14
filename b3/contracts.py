"""Contract months, expiries and the roll schedule of WIN and WDO.

Expiry rules (B3 contract specifications; confirm against the official expiry calendar in F1):
- WIN (mini Ibovespa): even months (G, J, M, Q, V, Z); expires on the Wednesday closest to the 15th
  of the month, or the next trading day if that Wednesday has no session. On expiry day the
  expiring contract stops trading at 17h (OC 005/2026-PRE, note 2), so a day trader must have
  rolled before.
- WDO (mini dollar): every month; expires on the first trading day of the contract month.

The roll rule is ex ante: the active contract switches `roll_days` trading days before the expiry
of the current one, so the strategy never trades a contract on its expiry day. The defaults below
are placeholders to be confirmed with the volume crossover of the two contracts (F1.5), and fixed
before the B3 splits are approved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import islice
from typing import Iterator

from b3.calendar import Holidays

MONTH_CODES = "FGHJKMNQUVXZ"            # January .. December
CONTRACT_MONTHS = {"WIN": (2, 4, 6, 8, 10, 12), "WDO": tuple(range(1, 13))}
DEFAULT_ROLL_DAYS = {"WIN": 2, "WDO": 2}
_CODE = re.compile(r"^(WIN|WDO)([FGHJKMNQUVXZ])(\d{2})$")


@dataclass(frozen=True)
class Contract:
    root: str
    year: int
    month: int
    expiry: date

    @property
    def code(self) -> str:
        return contract_code(self.root, self.year, self.month)


def contract_code(root: str, year: int, month: int) -> str:
    if month not in CONTRACT_MONTHS[root]:
        raise ValueError(f"{root} has no contract in month {month}")
    return f"{root}{MONTH_CODES[month - 1]}{year % 100:02d}"


def parse_code(code: str) -> tuple[str, int, int]:
    m = _CODE.match(code.upper())
    if not m:
        raise ValueError(f"{code!r} is not a WIN/WDO contract code like WINZ26")
    return m.group(1), 2000 + int(m.group(3)), MONTH_CODES.index(m.group(2)) + 1


def _wednesday_closest_to_15th(year: int, month: int) -> date:
    fifteenth = date(year, month, 15)
    delta = 2 - fifteenth.weekday()       # Wednesday is weekday 2
    if delta > 3:
        delta -= 7
    elif delta < -3:
        delta += 7
    return fifteenth + timedelta(days=delta)


def expiry(root: str, year: int, month: int, holidays: Holidays) -> date:
    root = root.upper()
    if month not in CONTRACT_MONTHS[root]:
        raise ValueError(f"{root} has no contract in month {month}")
    if root == "WIN":
        return holidays.next_trading_day(_wednesday_closest_to_15th(year, month), include_today=True)
    return holidays.next_trading_day(date(year, month, 1), include_today=True)


def contract(code: str, holidays: Holidays) -> Contract:
    root, year, month = parse_code(code)
    return Contract(root, year, month, expiry(root, year, month, holidays))


def iter_contracts(root: str, start: date, holidays: Holidays) -> Iterator[Contract]:
    """Consecutive contracts of `root` whose expiry is on or after `start`, computed lazily: a
    contract in a year without a holiday list raises only when it is actually needed."""
    root = root.upper()
    year, month = start.year, start.month
    while True:
        if month in CONTRACT_MONTHS[root]:
            c = Contract(root, year, month, expiry(root, year, month, holidays))
            if c.expiry >= start:
                yield c
        month += 1
        if month > 12:
            month, year = 1, year + 1


def contracts_from(root: str, start: date, count: int, holidays: Holidays) -> list[Contract]:
    """`count` consecutive contracts of `root` whose expiry is on or after `start`."""
    return list(islice(iter_contracts(root, start, holidays), count))


def roll_day(c: Contract, holidays: Holidays, roll_days: int) -> date:
    """First day on which the NEXT contract is the active one."""
    if roll_days < 1:
        raise ValueError("roll_days must be >= 1: the expiring contract closes early on expiry day")
    return holidays.add_trading_days(c.expiry, -roll_days)


def active_contract(root: str, day: date, holidays: Holidays, roll_days: int | None = None) -> Contract:
    """The contract a day trader uses on `day` under the ex-ante roll rule."""
    root = root.upper()
    n = DEFAULT_ROLL_DAYS[root] if roll_days is None else roll_days
    for c in islice(iter_contracts(root, day, holidays), 3):
        if day < roll_day(c, holidays, n):
            return c
    raise AssertionError("unreachable: three consecutive contracts cannot all be rolled past")


@dataclass(frozen=True)
class RollSegment:
    contract: Contract
    first_day: date     # first trading day this contract is active
    last_day: date      # last trading day it is active (inclusive)


def roll_schedule(root: str, start: date, end: date, holidays: Holidays,
                  roll_days: int | None = None) -> list[RollSegment]:
    """Which contract is active on each trading day of [start, end], as contiguous segments."""
    segments: list[RollSegment] = []
    for d in holidays.trading_days(start, end):
        c = active_contract(root, d, holidays, roll_days)
        if segments and segments[-1].contract == c:
            segments[-1] = RollSegment(c, segments[-1].first_day, d)
        else:
            segments.append(RollSegment(c, d, d))
    return segments
