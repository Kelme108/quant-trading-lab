from datetime import date

import pytest

from b3.calendar import Holidays, UnknownCalendarYear
from b3.contracts import (
    active_contract, contract, contract_code, contracts_from, expiry, parse_code, roll_day, roll_schedule,
)

H = Holidays.from_file()


def test_codes_round_trip():
    assert contract_code("WIN", 2026, 12) == "WINZ26"
    assert contract_code("WDO", 2026, 11) == "WDOX26"
    assert parse_code("wdoz26") == ("WDO", 2026, 12)
    with pytest.raises(ValueError):
        contract_code("WIN", 2026, 11)             # WIN has no odd months
    with pytest.raises(ValueError):
        parse_code("PETR4")


@pytest.mark.parametrize("month, expected", [
    (2, date(2026, 2, 18)),    # 15th is a Sunday -> Wed 18 (Ash Wednesday, a session from 13h)
    (4, date(2026, 4, 15)),    # 15th is a Wednesday
    (6, date(2026, 6, 17)),    # Mon 15 -> Wed 17
    (8, date(2026, 8, 12)),    # Sat 15 -> Wed 12 (3 days) beats Wed 19 (4 days)
    (10, date(2026, 10, 14)),  # Thu 15 -> Wed 14
    (12, date(2026, 12, 16)),  # Tue 15 -> Wed 16
])
def test_win_expires_on_the_wednesday_closest_to_the_15th(month, expected):
    assert expiry("WIN", 2026, month, H) == expected


@pytest.mark.parametrize("month, expected", [
    (1, date(2026, 1, 2)),     # Jan 1 closed
    (2, date(2026, 2, 2)),
    (5, date(2026, 5, 4)),     # Fri May 1 closed -> Mon 4
    (11, date(2026, 11, 3)),   # Mon Nov 2 (Finados) closed -> the WDOX26 in live.example.json expired here
    (12, date(2026, 12, 1)),
])
def test_wdo_expires_on_the_first_trading_day(month, expected):
    assert expiry("WDO", 2026, month, H) == expected


def test_today_active_contracts_and_roll_days():
    assert active_contract("WIN", date(2026, 11, 12), H).code == "WINZ26"
    assert active_contract("WDO", date(2026, 11, 12), H).code == "WDOZ26"
    z = contract("WINZ26", H)
    assert roll_day(z, H, 2) == date(2026, 12, 14)
    assert active_contract("WIN", date(2026, 12, 11), H).code == "WINZ26"
    with pytest.raises(UnknownCalendarYear):          # the next one needs the 2027 calendar
        active_contract("WIN", date(2026, 12, 14), H)
    with pytest.raises(ValueError):
        roll_day(z, H, 0)                              # never trade the expiring contract on expiry day


def test_roll_schedule_switches_before_expiry():
    segs = roll_schedule("WIN", date(2026, 9, 1), date(2026, 11, 30), H)
    assert [s.contract.code for s in segs] == ["WINV26", "WINZ26"]
    # WINV26 expires Wed Oct 14. Two trading days before it: Tue 13, (Mon 12 closed), Fri 9 -> the
    # next contract is active from Fri 9, so Thu 8 is the last day of WINV26.
    assert segs[0].last_day == date(2026, 10, 8)
    assert segs[1].first_day == date(2026, 10, 9)
    for s in segs:
        assert s.last_day < s.contract.expiry


def test_contracts_from_lists_in_order():
    assert [c.code for c in contracts_from("WDO", date(2026, 9, 2), 3, H)] == ["WDOV26", "WDOX26", "WDOZ26"]
