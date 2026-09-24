from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# check_same_thread=False: SQLite + de threadpool die FastAPI voor sync routes gebruikt.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

if settings.database_url.startswith("sqlite"):
    # SQLite negeert `ondelete="CASCADE"`/"SET NULL" op ForeignKey-kolommen (overal in
    # app/models/*.py) tenzij foreign-key-afdwinging per connectie expliciet aangezet
    # wordt -- zonder dit bleven bv. rijen in de tag-koppeltabellen (note_tags e.d.)
    # na een bulk-delete (Query.delete(), dat buiten de ORM om gaat) als "wees" achter,
    # en konden die per ongeluk aan een nieuwe rij "vastplakken" zodra SQLite hetzelfde
    # primary-key-id hergebruikte voor een latere, ongerelateerde rij.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
