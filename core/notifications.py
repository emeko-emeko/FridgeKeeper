"""Расчёт уведомлений о сроке годности. Чистые функции: удобно тестировать."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Almaty")  # Астана = UTC+5
LEVELS: tuple[int, ...] = (24, 12, 6, 2)  # часы до дедлайна


def deadline_for(expiry_date: date) -> datetime:
    """Дедлайн: 00:00 дня, следующего за датой на этикетке.

    «Годен до 12.05» означает, что продукт годен весь 12 мая, поэтому дедлайн — 13.05 00:00.
    """
    return datetime.combine(expiry_date + timedelta(days=1), time.min, tzinfo=TZ)


@dataclass(frozen=True)
class Decision:
    send_level: int | None        # за сколько часов отправить уведомление (None — ничего)
    skip_levels: tuple[int, ...]  # уровни, которые пропускаем, но помечаем обработанными


def decide(deadline: datetime, now: datetime, handled: set[int]) -> Decision:
    """Что отправить сейчас.

    Если наступило несколько уровней (например, ПК был выключен), отправляется одно
    сообщение для самого срочного, остальные уровни помечаются как пропущенные.
    """
    remaining = deadline - now
    if remaining <= timedelta(0):
        return Decision(None, ())

    due = [lvl for lvl in LEVELS if lvl not in handled and remaining <= timedelta(hours=lvl)]
    if not due:
        return Decision(None, ())

    chosen = min(due)  # самый маленький уровень = самый срочный
    return Decision(chosen, tuple(lvl for lvl in due if lvl != chosen))


def build_message(product_name: str, deadline: datetime, now: datetime) -> str:
    """Текст уведомления с реальным оставшимся временем."""
    hours = max(1, int((deadline - now).total_seconds() // 3600) + 1)
    return f"Срок годности «{product_name}» истекает примерно через {hours} ч."