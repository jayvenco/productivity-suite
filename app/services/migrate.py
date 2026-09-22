from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Lichte, additive kolom-migraties voor SQLite. Er is bewust geen Alembic
# opgetuigd voor deze schaal; dit voorkomt alleen dat bestaande installaties
# (bv. op Unraid) hun data kwijtraken wanneer een model een kolom krijgt.
_COLUMNS_TO_ENSURE = {
    "tasks": [("priority", "BOOLEAN DEFAULT 0")],
    "kanban_cards": [("color", "VARCHAR(20)")],
    "kanban_columns": [("swimlane_id", "INTEGER")],
    "notes": [("is_temp", "BOOLEAN DEFAULT 0")],
    "mindmap_boards": [("description", "TEXT DEFAULT ''")],
    "users": [
        ("font_family", "VARCHAR(50) DEFAULT 'system'"),
        ("font_size", "INTEGER DEFAULT 14"),
        ("density", "VARCHAR(20) DEFAULT 'comfortable'"),
        ("background", "VARCHAR(30) DEFAULT 'none'"),
        ("background_opacity", "INTEGER DEFAULT 30"),
        ("api_token_hash", "VARCHAR(64)"),
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
