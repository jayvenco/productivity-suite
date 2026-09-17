import re


def test_notes_requires_login(client):
    response = client.get("/notes", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_and_list_note(logged_in_client):
    response = logged_in_client.post(
        "/notes",
        data={
            "title": "Vergaderverslag",
            "content": "<h2>Kop</h2><p>Een <strong>belangrijk</strong> punt.</p>",
            "tags": "werk, meeting",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    listing = logged_in_client.get("/notes")
    assert listing.status_code == 200
    assert "Vergaderverslag" in listing.text
    assert "werk" in listing.text
    assert "<strong>belangrijk</strong>" in listing.text


def test_note_html_is_sanitized(logged_in_client):
    logged_in_client.post(
        "/notes",
        data={
            "title": "Gevaarlijke notitie",
            "content": "<p>Hallo</p><script>alert('x')</script><img src=x onerror=alert(1)>",
            "tags": "",
        },
    )
    listing = logged_in_client.get("/notes").text
    assert "<script>" not in listing
    assert "onerror" not in listing
    assert "Hallo" in listing


def test_edit_note(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Origineel", "content": "<p>tekst</p>", "tags": ""})
    listing = logged_in_client.get("/notes").text
    match = re.search(r'/notes/(\d+)/edit"[^>]*>Origineel<', listing)
    assert match, "Notitie niet gevonden"
    note_id = match.group(1)

    update = logged_in_client.post(
        f"/notes/{note_id}",
        data={"title": "Bijgewerkt", "content": "<p>nieuwe tekst</p>", "tags": "belangrijk"},
        follow_redirects=False,
    )
    assert update.status_code == 303

    listing_after = logged_in_client.get("/notes").text
    assert "Bijgewerkt" in listing_after
    assert "Origineel" not in listing_after
    assert "belangrijk" in listing_after


def test_delete_note(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Te verwijderen", "content": "", "tags": ""})
    listing = logged_in_client.get("/notes").text
    match = re.search(r'/notes/(\d+)/edit"[^>]*>Te verwijderen<', listing)
    note_id = match.group(1)

    response = logged_in_client.post(f"/notes/{note_id}/delete", follow_redirects=False)
    assert response.status_code == 303

    listing_after = logged_in_client.get("/notes").text
    assert "Te verwijderen" not in listing_after


def test_filter_notes_by_tag(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Werknotitie", "content": "", "tags": "werk"})
    logged_in_client.post("/notes", data={"title": "Privenotitie", "content": "", "tags": "prive"})

    filtered = logged_in_client.get("/notes?tag=werk").text
    assert "Werknotitie" in filtered
    assert "Privenotitie" not in filtered
