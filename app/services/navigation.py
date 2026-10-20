"""Modules die in het navigatiemenu (de ribbon) getoond kunnen worden. De gebruiker kan er
onder Account -> Navigatie per module één aan- of uitzetten (User.hidden_modules)."""

from __future__ import annotations

NAV_MODULES = [
    ("tasks", "Taken"),
    ("kanban", "Kanban"),
    ("mindmap", "Mindmap"),
    ("notes", "Notities"),
    ("pomodoro", "Pomodoro"),
    ("stickies", "Stickies"),
    ("snippets", "Snippets"),
    ("calendar", "Kalender"),
    ("search", "Zoeken"),
    ("graph", "Graph"),
    ("stats", "Statistieken"),
]
NAV_MODULE_KEYS = {key for key, _ in NAV_MODULES}
# Statistieken staat standaard uit (zie de migratie in app/services/migrate.py).
DEFAULT_HIDDEN = "stats"


def parse_hidden(raw: str | None) -> set[str]:
    return {k for k in (raw or "").split(",") if k in NAV_MODULE_KEYS}
