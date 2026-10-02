from __future__ import annotations

import calendar
from datetime import date, timedelta

RECURRENCE_LABELS = {"none": "Niet herhalen", "weekly": "Elke week", "monthly": "Elke maand"}


def _monthly_date(start: date, index: int) -> date:
    month_index = start.month - 1 + index
    year, month = start.year + month_index // 12, month_index % 12 + 1
    # 31 januari + 1 maand = laatste dag van februari i.p.v. een ongeldige datum
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def occurrences(start: date, recurrence: str, until: date | None, range_start: date, range_end: date) -> list[date]:
    """Alle voorkomens van een (herhalende) afspraak binnen [range_start, range_end]."""
    last = min(range_end, until) if until else range_end
    if recurrence not in ("weekly", "monthly"):
        return [start] if range_start <= start <= range_end else []

    result: list[date] = []
    if recurrence == "weekly":
        current = start
        if current < range_start:
            current += timedelta(weeks=(range_start - current).days // 7)
            if current < range_start:
                current += timedelta(weeks=1)
        while current <= last:
            result.append(current)
            current += timedelta(weeks=1)
        return result

    index = 0
    if range_start > start:
        index = max(0, (range_start.year - start.year) * 12 + range_start.month - start.month - 1)
    while True:
        current = _monthly_date(start, index)
        if current > last:
            return result
        if current >= range_start:
            result.append(current)
        index += 1


def next_occurrence(start: date, recurrence: str, until: date | None, today: date) -> date | None:
    found = occurrences(start, recurrence, until, today, today + timedelta(days=400))
    return found[0] if found else None
