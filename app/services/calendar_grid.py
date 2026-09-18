from __future__ import annotations

import calendar
from datetime import date, timedelta

# Vaste Nederlandse namen i.p.v. calendar.month_name/day_name: die zijn
# locale-afhankelijk, en de container heeft geen Nederlandse locale ingesteld.
DUTCH_MONTHS = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
]
DUTCH_WEEKDAYS = ["ma", "di", "wo", "do", "vr", "za", "zo"]

_calendar = calendar.Calendar(firstweekday=0)  # 0 = maandag


def month_weeks(year: int, month: int) -> list[list[date]]:
    """Volle weken (ma-zo) die deze maand overlappen, inclusief de dagen uit de
    vorige/volgende maand die de eerste/laatste week opvullen."""
    return list(_calendar.monthdatescalendar(year, month))


def week_dates(reference: date) -> list[date]:
    """De 7 dagen (ma t/m zo) van de week die `reference` bevat."""
    monday = reference - timedelta(days=reference.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    """Jaar/maand delta maanden verschoven, met correcte jaarovergang."""
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1
