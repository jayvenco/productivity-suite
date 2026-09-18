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

    filtered = logged_in_client.get("/notes?tags=werk").text
    assert "Werknotitie" in filtered
    assert "Privenotitie" not in filtered


def test_filter_notes_by_multiple_tags_is_or(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Werknotitie", "content": "", "tags": "werk"})
    logged_in_client.post("/notes", data={"title": "Privenotitie", "content": "", "tags": "prive"})
    logged_in_client.post("/notes", data={"title": "Sportnotitie", "content": "", "tags": "sport"})

    filtered = logged_in_client.get("/notes?tags=werk&tags=prive").text
    assert "Werknotitie" in filtered
    assert "Privenotitie" in filtered
    assert "Sportnotitie" not in filtered


def test_note_tag_filter_checkboxes_listed_and_checked(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Werknotitie", "content": "", "tags": "werk"})

    page = logged_in_client.get("/notes?tags=werk").text
    assert 'name="tags" value="werk"' in page
    checkbox = re.search(r'<input type="checkbox" form="notes-tag-filter-form" name="tags" value="werk"[^>]*>', page).group(0)
    assert "checked" in checkbox


def test_note_card_has_no_tag_color_tint(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Geen tint", "content": "", "tags": "werk"})
    listing = logged_in_client.get("/notes").text
    assert not re.search(r'class="note-card"[^>]*style="[^"]*hsla', listing)


def _note_ids_for_titles(html: str, titles: list[str]) -> list[str]:
    ids = []
    for title in titles:
        match = re.search(rf'/notes/(\d+)/edit"[^>]*>{re.escape(title)}<', html)
        assert match, f"Notitie met titel {title!r} niet gevonden"
        ids.append(match.group(1))
    return ids


def test_bulk_delete_notes(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Bulk een", "content": "", "tags": ""})
    logged_in_client.post("/notes", data={"title": "Bulk twee", "content": "", "tags": ""})
    logged_in_client.post("/notes", data={"title": "Blijft staan", "content": "", "tags": ""})

    listing = logged_in_client.get("/notes").text
    ids = _note_ids_for_titles(listing, ["Bulk een", "Bulk twee"])

    response = logged_in_client.post(
        "/notes/bulk-delete", data={"note_ids": ids}, follow_redirects=False
    )
    assert response.status_code == 303

    listing_after = logged_in_client.get("/notes").text
    assert "Bulk een" not in listing_after
    assert "Bulk twee" not in listing_after
    assert "Blijft staan" in listing_after


def test_bulk_tag_notes(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Bulktag een", "content": "", "tags": ""})
    logged_in_client.post("/notes", data={"title": "Bulktag twee", "content": "", "tags": "bestaand"})

    listing = logged_in_client.get("/notes").text
    ids = _note_ids_for_titles(listing, ["Bulktag een", "Bulktag twee"])

    response = logged_in_client.post(
        "/notes/bulk-tag", data={"note_ids": ids, "tag": "gedeeld"}, follow_redirects=False
    )
    assert response.status_code == 303

    filtered = logged_in_client.get("/notes?tags=gedeeld").text
    assert "Bulktag een" in filtered
    assert "Bulktag twee" in filtered

    # Bestaande tag van de tweede notitie moet behouden blijven.
    listing_after = logged_in_client.get("/notes").text
    assert "bestaand" in listing_after
