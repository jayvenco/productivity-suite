import re


def test_notes_requires_login(client):
    response = client.get("/notes", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_and_list_note(logged_in_client):
    response = logged_in_client.post(
        "/notes",
        data={"title": "Vergaderverslag", "content": "# Kop\n\nEen **belangrijk** punt.", "tags": "werk, meeting"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    listing = logged_in_client.get("/notes")
    assert listing.status_code == 200
    assert "Vergaderverslag" in listing.text
    assert "werk" in listing.text
    # Markdown moet gerenderd zijn (niet als ruwe tekst getoond worden).
    assert "<strong>belangrijk</strong>" in listing.text
    assert "**belangrijk**" not in listing.text


def test_edit_note(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Origineel", "content": "tekst", "tags": ""})
    listing = logged_in_client.get("/notes").text
    match = re.search(r'/notes/(\d+)/edit"[^>]*>Origineel<', listing)
    assert match, "Notitie niet gevonden"
    note_id = match.group(1)

    update = logged_in_client.post(
        f"/notes/{note_id}",
        data={"title": "Bijgewerkt", "content": "nieuwe tekst", "tags": "belangrijk"},
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


def test_preview_endpoint_renders_markdown(logged_in_client):
    response = logged_in_client.post("/notes/preview", data={"content": "**vet** en *cursief*"})
    assert response.status_code == 200
    assert "<strong>vet</strong>" in response.text
    assert "<em>cursief</em>" in response.text


def test_preview_requires_login(client):
    response = client.post("/notes/preview", data={"content": "test"}, follow_redirects=False)
    assert response.status_code == 303
