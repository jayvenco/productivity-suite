import json
import time
from datetime import datetime

from app.database import SessionLocal
from app.models.snippet import Snippet, SnippetFile
from app.models.user import User
from app.services import backup


def _point_backup_at(tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "BACKUP_DIR", tmp_path)
    monkeypatch.setattr(backup, "SNIPPET_BACKUP_DIR", tmp_path / "snippets")


def test_database_backup_is_created_once_per_day_and_pruned(client, tmp_path, monkeypatch):
    _point_backup_at(tmp_path, monkeypatch)
    for day in ["20200101", "20200102", "20200103"]:
        (tmp_path / f"app-{day}.db").write_bytes(b"oud")

    created = backup.backup_database(keep=2)
    assert created is not None and created.name == f"app-{datetime.now():%Y%m%d}.db"
    assert backup.backup_database(keep=2) is None  # vandaag staat er al een

    names = sorted(p.name for p in tmp_path.glob("app-*.db"))
    assert names == ["app-20200103.db", created.name]


def test_snippet_backup_only_writes_new_or_changed_and_keeps_deleted(client, tmp_path, monkeypatch):
    _point_backup_at(tmp_path, monkeypatch)
    with SessionLocal() as db:
        user = db.query(User).first()
        snippet = Snippet(user_id=user.id, title="Backup-snippet", description="d")
        snippet.files = [SnippetFile(filename="a.py", language="python", content="print(1)", position=0)]
        db.add(snippet)
        db.commit()
        snippet_id = snippet.id

        assert backup.backup_snippets(db) >= 1
        assert backup.backup_snippets(db) == 0  # niets nieuws of gewijzigd

        data = json.loads((tmp_path / "snippets" / f"{snippet_id}.json").read_text())
        assert data["title"] == "Backup-snippet"
        assert data["files"][0]["content"] == "print(1)"

        snippet.files[0].content = "print(2)"
        db.commit()
        assert backup.backup_snippets(db) == 1

        db.delete(snippet)
        db.commit()
        backup.backup_snippets(db)
        assert (tmp_path / "snippets" / f"{snippet_id}.json").exists()


def test_monthly_backup_once_per_month_list_and_restore(logged_in_client, tmp_path, monkeypatch):
    monkeypatch.setattr(backup, "MONTHLY_DIR", tmp_path / "backup")
    first = backup.backup_monthly()
    assert first is not None and first.exists()
    assert backup.backup_monthly() is None  # deze maand staat er al een
    manual = backup.backup_monthly(force=True)
    assert manual is not None
    assert len(backup.list_monthly_backups()) == 2
    assert backup.resolve_monthly_backup("../x.db") is None

    page = logged_in_client.get("/account")
    assert first.name in page.text and "Nu een back-up maken" in page.text
    time.sleep(1.1)  # handmatige back-ups heten op de seconde nauwkeurig
    assert logged_in_client.post("/account/backup/monthly/run", follow_redirects=False).status_code == 303
    assert len(backup.list_monthly_backups()) == 3
    assert logged_in_client.get(f"/account/backup/monthly/{first.name}/download").status_code == 200
    assert logged_in_client.post("/account/backup/monthly/nietbestaand.db/restore").status_code == 400
    r = logged_in_client.post(f"/account/backup/monthly/{first.name}/restore", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
