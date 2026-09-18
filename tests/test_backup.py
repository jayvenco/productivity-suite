def test_export_requires_login(client):
    response = client.get("/account/backup/export", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_export_returns_sqlite_file(logged_in_client):
    response = logged_in_client.get("/account/backup/export")
    assert response.status_code == 200
    assert response.content.startswith(b"SQLite format 3\x00")
    assert "productivity-suite-backup-" in response.headers["content-disposition"]


def test_import_rejects_non_sqlite_file(logged_in_client):
    response = logged_in_client.post(
        "/account/backup/import",
        files={"backup_file": ("niet-een-db.txt", b"dit is geen database", "text/plain")},
    )
    assert response.status_code == 400
    assert "geen geldig SQLite" in response.text


def test_import_rejects_sqlite_file_without_expected_tables(logged_in_client):
    import sqlite3
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        conn = sqlite3.connect(tmp.name)
        conn.execute("CREATE TABLE willekeurig (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        tmp.seek(0)
        content = tmp.read()

    response = logged_in_client.post(
        "/account/backup/import",
        files={"backup_file": ("vreemd.db", content, "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "geen Productivity Suite-back-up" in response.text


def test_export_then_import_round_trip_restores_old_state(logged_in_client):
    # Bewaar de staat van vóór deze test, zodat we die aan het eind kunnen
    # terugzetten -- deze test vervangt de hele database, en andere testmodules
    # in dezelfde sessie draaien op diezelfde (gedeelde) database.
    original_backup = logged_in_client.get("/account/backup/export").content

    logged_in_client.post("/tasks", data={"title": "Voor backup", "description": "", "deadline": "", "tags": ""})
    backup_bytes = logged_in_client.get("/account/backup/export").content

    logged_in_client.post("/tasks", data={"title": "Na backup", "description": "", "deadline": "", "tags": ""})
    before_restore = logged_in_client.get("/tasks").text
    assert "Voor backup" in before_restore
    assert "Na backup" in before_restore

    response = logged_in_client.post(
        "/account/backup/import",
        files={"backup_file": ("backup.db", backup_bytes, "application/octet-stream")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    logged_in_client.post("/login", data={"username": "admin", "password": "testpass"})
    after_restore = logged_in_client.get("/tasks").text
    assert "Voor backup" in after_restore
    assert "Na backup" not in after_restore

    # Staat van vóór deze test terugzetten voor de rest van de testsessie.
    logged_in_client.post(
        "/account/backup/import",
        files={"backup_file": ("original.db", original_backup, "application/octet-stream")},
    )
    logged_in_client.post("/login", data={"username": "admin", "password": "testpass"})
