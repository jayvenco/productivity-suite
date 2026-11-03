"""Voortgang per swimlane: hoe ver zijn de aanwezige, opgepakte en gedane werkzaamheden?

Elke kolom telt mee naar haar positie in de swimlane: de eerste kolom (bv. Backlog) is 0%, de
laatste (bv. Done) 100%, de kolommen ertussen lopen lineair op (bij 5 kolommen: 0/25/50/75/100%).
De voortgang is het gemiddelde over alle kaarten in die swimlane. Dezelfde formule staat in
app/static/js/kanban.js (live bijwerken na slepen) -- pas ze samen aan."""

from __future__ import annotations

DOTS = 10


def swimlane_progress(card_counts_per_column: list[int]) -> dict:
    """card_counts_per_column: aantal kaarten per kolom, in kolomvolgorde (links -> rechts)."""
    columns = len(card_counts_per_column)
    total = sum(card_counts_per_column)
    if total == 0 or columns < 2:
        percent = 0
    else:
        weighted = sum(count * index / (columns - 1) for index, count in enumerate(card_counts_per_column))
        percent = round(100 * weighted / total)
    return {"percent": percent, "cards": total, "filled": int(percent / 10 + 0.5)}
