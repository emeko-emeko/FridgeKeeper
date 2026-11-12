# tests/test_notifications.py
from datetime import date, datetime

from core.notifications import TZ, decide, deadline_for

DEADLINE = deadline_for(date(2027, 5, 12))  # 13.05.2027 00:00


def dt(day: int, hour: int) -> datetime:
    return datetime(2027, 5, day, hour, tzinfo=TZ)


def test_deadline_is_next_day_midnight():
    assert DEADLINE == datetime(2027, 5, 13, 0, 0, tzinfo=TZ)


def test_regular_levels_fire_at_their_time():
    assert decide(DEADLINE, dt(12, 0), set()).send_level == 24
    assert decide(DEADLINE, dt(12, 12), {24}).send_level == 12
    assert decide(DEADLINE, dt(12, 18), {24, 12}).send_level == 6
    assert decide(DEADLINE, dt(12, 22), {24, 12, 6}).send_level == 2


def test_restart_sends_one_message_and_skips_rest():
    # ПК был выключен с 11:00 до 13:00 — уровни 24 и 12 наступили
    decision = decide(DEADLINE, dt(12, 13), {24})
    assert decision.send_level == 12
    assert decision.skip_levels == ()


def test_added_with_one_hour_left_sends_single_message():
    decision = decide(DEADLINE, datetime(2027, 5, 12, 23, tzinfo=TZ), set())
    assert decision.send_level == 2
    assert set(decision.skip_levels) == {24, 12, 6}


def test_nothing_after_deadline():
    assert decide(DEADLINE, datetime(2027, 5, 13, 1, tzinfo=TZ), set()).send_level is None