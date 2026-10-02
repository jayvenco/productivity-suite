from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session, selectinload

from app.config import DATA_DIR, settings
from app.database import SessionLocal
from app.models.snippet import Snippet

log = logging.getLogger(__name__)

BACKUP_DIR = DATA_DIR / "backups"
SNIPPET_BACKUP_DIR = BACKUP_DIR / "snippets"
_DB_BACKUP_PREFIX = "app-"


def _db_path() -> Path:
    return Path(settings.database_url.removeprefix("sqlite:///"))


def backup_database(keep: int | None = None) -> Path | None:
    """Maakt hooguit één database-backup per dag (VACUUM INTO, veilig naast een lopende
    app) en bewaart alleen de nieuwste `keep` stuks. Geeft het pad terug als er een
    backup gemaakt is, anders None."""
    keep = keep if keep is not None else settings.backup_keep
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"{_DB_BACKUP_PREFIX}{datetime.now():%Y%m%d}.db"
    created = None
    if not target.exists():
        conn = sqlite3.connect(_db_path())
        try:
            conn.execute("VACUUM INTO ?", (str(target),))
        finally:
            conn.close()
        created = target

    old = sorted(BACKUP_DIR.glob(f"{_DB_BACKUP_PREFIX}*.db"))[:-keep] if keep > 0 else []
    for path in old:
        path.unlink(missing_ok=True)
    return created


def _snippet_payload(snippet: Snippet) -> str:
    return json.dumps(
        {
            "id": snippet.id,
            "title": snippet.title,
            "description": snippet.description,
            "tags": [t.name for t in snippet.tags],
            "created_at": snippet.created_at.isoformat() if snippet.created_at else None,
            "updated_at": snippet.updated_at.isoformat() if snippet.updated_at else None,
            "files": [
                {"filename": f.filename, "language": f.language, "content": f.content}
                for f in snippet.files
            ],
        },
        ensure_ascii=False,
        indent=2,
    )


def backup_snippets(db: Session) -> int:
    """Schrijft elke snippet als eigen JSON-bestand weg, maar alleen als die er nog niet
    staat of inhoudelijk gewijzigd is -- en verwijdert nooit iets, dus ook een inmiddels
    uit de app verwijderde snippet blijft in de backup staan. Geeft het aantal
    (nieuw/bijgewerkt) weggeschreven snippets terug."""
    SNIPPET_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    snippets = db.query(Snippet).options(selectinload(Snippet.files), selectinload(Snippet.tags)).all()
    for snippet in snippets:
        path = SNIPPET_BACKUP_DIR / f"{snippet.id}.json"
        payload = _snippet_payload(snippet)
        if path.exists() and path.read_text(encoding="utf-8") == payload:
            continue
        path.write_text(payload, encoding="utf-8")
        written += 1
    return written


def run_backup() -> None:
    try:
        backup_database()
        with SessionLocal() as db:
            backup_snippets(db)
    except Exception:  # een mislukte backup mag de app nooit onderuit halen
        log.exception("Automatische backup mislukt")


def start_backup_scheduler() -> None:
    """Draait meteen één backup en daarna elk uur opnieuw (de dagelijkse database-backup
    slaat zichzelf over als er vandaag al een staat; nieuwe/gewijzigde snippets worden dus
    binnen een uur meegenomen). Daemon-thread: geen extra container/cron nodig."""
    if not settings.backup_enabled:
        return

    def loop() -> None:
        while True:
            run_backup()
            threading.Event().wait(60 * 60)

    threading.Thread(target=loop, name="auto-backup", daemon=True).start()
