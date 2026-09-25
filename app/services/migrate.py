from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Lichte, additive kolom-migraties voor SQLite. Er is bewust geen Alembic
# opgetuigd voor deze schaal; dit voorkomt alleen dat bestaande installaties
# (bv. op Unraid) hun data kwijtraken wanneer een model een kolom krijgt.
_COLUMNS_TO_ENSURE = {
    "tasks": [("priority", "BOOLEAN DEFAULT 0"), ("daily_task", "BOOLEAN DEFAULT 0")],
    "kanban_cards": [("color", "VARCHAR(20)")],
    "kanban_columns": [("swimlane_id", "INTEGER")],
    "kanban_swimlanes": [("color", "VARCHAR(20)")],
    "notes": [("is_temp", "BOOLEAN DEFAULT 0")],
    "mindmap_boards": [("description", "TEXT DEFAULT ''")],
    "users": [
        ("font_family", "VARCHAR(50) DEFAULT 'system'"),
        ("font_size", "INTEGER DEFAULT 14"),
        ("density", "VARCHAR(20) DEFAULT 'comfortable'"),
        ("background", "VARCHAR(30) DEFAULT 'none'"),
        ("background_opacity", "INTEGER DEFAULT 30"),
        ("api_token_hash", "VARCHAR(64)"),
        ("openai_api_key", "VARCHAR(255)"),
    ],
}


def run_lightweight_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        added_swimlane_id_column = False

        for table, columns in _COLUMNS_TO_ENSURE.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for column_name, column_def in columns:
                if column_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}"))
                    if table == "kanban_columns" and column_name == "swimlane_id":
                        added_swimlane_id_column = True

        if added_swimlane_id_column:
            _backfill_column_swimlanes(conn)

        _cleanup_orphaned_tag_associations(conn)


# (koppeltabel, kolom die naar het getagde item wijst, tabel van dat item) -- vóór
# `PRAGMA foreign_keys=ON` (zie app/database.py) kon een bulk-delete (Query.delete(),
# gaat buiten de ORM om) een rij hier laten staan nadat het getagde item allang weg was;
# zodra SQLite hetzelfde id later hergebruikte voor een nieuwe, ongerelateerde rij "erfde"
# die er per ongeluk de oude tags van. Draait bij elke start opnieuw (goedkoop, en
# idempotent op een schone database) zodat ook al bestaande installaties hiervan herstellen.
_TAG_ASSOCIATION_TABLES = [
    ("task_tags", "task_id", "tasks"),
    ("card_tags", "card_id", "kanban_cards"),
    ("note_tags", "note_id", "notes"),
    ("snippet_tags", "snippet_id", "snippets"),
    ("event_tags", "event_id", "calendar_events"),
    ("mindmap_tags", "mindmap_board_id", "mindmap_boards"),
]


def _cleanup_orphaned_tag_associations(conn) -> None:
    existing_tables = {row[0] for row in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
    for assoc_table, fk_column, parent_table in _TAG_ASSOCIATION_TABLES:
        if assoc_table not in existing_tables or parent_table not in existing_tables:
            continue
        conn.execute(
            text(
                f"DELETE FROM {assoc_table} WHERE {fk_column} NOT IN (SELECT id FROM {parent_table})"  # noqa: S608
            )
        )


def _backfill_column_swimlanes(conn) -> None:
    """Kolommen zaten vóór deze migratie direct aan het bord vast, niet aan een
    swimlane. Wijs bestaande kolommen toe aan de (eerste) swimlane van hun bord,
    zodat oude data blijft werken met het nieuwe per-swimlane kolommenmodel."""
    rows = conn.execute(
        text("SELECT id, board_id FROM kanban_columns WHERE swimlane_id IS NULL")
    ).fetchall()
    for column_id, board_id in rows:
        swimlane = conn.execute(
            text("SELECT id FROM kanban_swimlanes WHERE board_id = :board_id ORDER BY position LIMIT 1"),
            {"board_id": board_id},
        ).first()
        if swimlane is not None:
            conn.execute(
                text("UPDATE kanban_columns SET swimlane_id = :swimlane_id WHERE id = :column_id"),
                {"swimlane_id": swimlane[0], "column_id": column_id},
            )
