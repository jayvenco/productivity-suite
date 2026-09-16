from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

# Lichte, additive kolom-migraties voor SQLite. Er is bewust geen Alembic
# opgetuigd voor deze schaal; dit voorkomt alleen dat bestaande installaties
# (bv. op Unraid) hun data kwijtraken wanneer een model een kolom krijgt.
_COLUMNS_TO_ENSURE = {
    "tasks": [("priority", "BOOLEAN DEFAULT 0")],
    "kanban_cards": [("color", "VARCHAR(20)")],
}


def run_lightweight_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        for table, columns in _COLUMNS_TO_ENSURE.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for column_name, column_def in columns:
                if column_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}"))
