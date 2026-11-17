from datetime import date, datetime, time, timedelta, timezone

import pytest

from b3.calendar import (
    SP_TZ, B3SessionCalendar, Holidays, SessionPeriod, SessionRules, SessionTable, UnknownCalendarYear,
    UnknownSession, infer_closed_weekdays, infer_session_table,
)
from b3_helpers import session_times

UTC = timezone.utc


def test_official_2026_list_loads_and_matches_the_circular():
    h = Holidays.from_file()
    assert h.known_years == {2026}
    assert len(h.closed) == 14                      # OC 041/2026-VNC, Quadro A
    for d in ("2026-11-20", "2026-11-02", "2026-12-24", "2026-12-31", "2026-02-16", "2026-02-17"):
        assert not h.is_trading_day(date.fromisoformat(d))
    assert h.is_trading_day(date(2026, 7, 9))        # Sao Paulo holiday, B3 opens
    assert h.is_trading_day(date(2026, 11, 12))
    assert not h.is_trading_day(date(2026, 11, 14))  # Saturday
    assert h.special_open_time(date(2026, 2, 18)) == time(13, 0)


def test_unknown_years_raise_instead_of_guessing():
    h = Holidays.from_file()
    with pytest.raises(UnknownCalendarYear):
        h.is_trading_day(date(2027, 1, 4))
    with pytest.raises(UnknownCalendarYear):
        h.is_trading_day(date(2019, 6, 3))
    assert h.is_trading_day(date(2027, 1, 2)) is False  # weekends need no list


def test_inferred_years_are_added_but_never_override_official_ones():
    h = Holidays.from_file().with_inferred([date(2025, 12, 25)], [2025], "test")
    assert not h.is_trading_day(date(2025, 12, 25)) and h.is_trading_day(date(2025, 12, 26))
    with pytest.raises(ValueError):
        Holidays.from_file().with_inferred([], [2026], "test")


def test_trading_day_arithmetic_skips_holidays():
    h = Holidays.from_file()
    assert h.add_trading_days(date(2026, 11, 19), 1) == date(2026, 11, 23)   # Fri 20 is closed
    assert h.add_trading_days(date(2026, 11, 3), -1) == date(2026, 10, 30)   # Mon 2 is closed
    assert h.next_trading_day(date(2026, 11, 2), include_today=True) == date(2026, 11, 3)
    assert len(h.trading_days(date(2026, 11, 16), date(2026, 11, 22))) == 4


def test_session_table_from_file_and_unknown_periods():
    s = SessionTable.from_file()
    p = s.period("WIN", date(2026, 11, 12))
    assert (p.open, p.close, p.expiry_close) == (time(9, 0), time(18, 25), time(17, 0))
    assert s.period("WDO", date(2026, 11, 12)).close == time(18, 30)
    with pytest.raises(UnknownSession):
        s.period("WIN", date(2021, 11, 12))                   # before the first inferred period (2021-11-16)
    assert s.period("WIN", date(2022, 6, 1)).close == time(17, 55)   # inferred: US summer 2022
    assert "INFERRED" in s.period("WIN", date(2026, 1, 5)).source
    with pytest.raises(ValueError):
        s.with_periods([SessionPeriod("WIN", date(2026, 6, 1), date(2026, 6, 30), time(9), time(18))])


def test_phases_of_a_win_session():
    cal = B3SessionCalendar("WIN", rules=SessionRules(15, 30, 10))
    at = lambda h, m: datetime(2026, 11, 12, h, m, tzinfo=SP_TZ)  # noqa: E731
    assert cal.phase(at(8, 59)) == "closed"
    assert cal.phase(at(9, 0)) == "no_entry"
    assert cal.phase(at(9, 15)) == "entry"
    assert cal.phase(at(17, 54)) == "entry"
    assert cal.phase(at(17, 55)) == "no_entry"
    assert cal.phase(at(18, 15)) == "flatten"
    assert cal.phase(at(18, 25)) == "closed"
    assert cal.phase(datetime(2026, 11, 20, 12, tzinfo=SP_TZ)) == "closed"   # holiday
    assert cal.day_key(at(10, 0)) == "2026-11-12"


def test_ash_wednesday_opens_late():
    cal = B3SessionCalendar("WIN")                            # 2026-01..03 hours come from the inferred period
    assert cal.phase(datetime(2026, 2, 18, 10, tzinfo=SP_TZ)) == "closed"
    assert cal.session(date(2026, 2, 18)).open.time() == time(13, 0)
    # a rule whose entry window cannot fit the late open simply has no session that day (P-021 crashed on it)
    late = B3SessionCalendar("WDO", rules=SessionRules(300, 44, 5))
    assert late.session(date(2026, 2, 18)) is None and late.session(date(2026, 2, 19)) is not None
    assert late.phase(datetime(2026, 2, 18, 15, tzinfo=SP_TZ)) == "closed"


def test_local_time_follows_brazil_dst_before_2019():
    h = Holidays.from_file().with_inferred([], [2018], "test")
    sessions = SessionTable((SessionPeriod("WIN", date(2018, 1, 1), date(2018, 12, 31), time(9), time(17, 55)),))
    cal = B3SessionCalendar("WIN", holidays=h, sessions=sessions)
    jan = cal.session(date(2018, 1, 10)).open.astimezone(UTC)    # Brazilian summer time, UTC-2
    jul = cal.session(date(2018, 7, 10)).open.astimezone(UTC)    # UTC-3
    assert (jan.hour, jul.hour) == (11, 12)


def test_rules_must_fit_and_be_ordered():
    with pytest.raises(ValueError):
        SessionRules(entry_end_before_close_min=5, flatten_before_close_min=10)
    cal = B3SessionCalendar("WIN", rules=SessionRules(600, 600, 10))
    with pytest.raises(ValueError):
        cal.session(date(2026, 11, 12))


def test_infer_session_table_and_closed_weekdays():
    times = session_times([date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 12)])
    periods = infer_session_table(times, "WIN", 5, "test")
    assert len(periods) == 1 and (periods[0].open, periods[0].close) == (time(9), time(18, 25))
    days = {t.astimezone(SP_TZ).date() for t in times}
    assert infer_closed_weekdays(days, date(2026, 11, 9), date(2026, 11, 13)) == [date(2026, 11, 11), date(2026, 11, 13)]
