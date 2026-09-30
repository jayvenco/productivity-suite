import json
import re


def test_snippets_requires_login(client):
    response = client.get("/snippets", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_create_and_list_snippet_with_single_file(logged_in_client):
    response = logged_in_client.post(
        "/snippets",
        data={
            "title": "Hello world script",
            "tags": "python, voorbeeld",
            "filename": ["main.py"],
            "language": ["python"],
            "content": ["print('hello')"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    listing = logged_in_client.get("/snippets")
    assert listing.status_code == 200
    assert "Hello world script" in listing.text
    assert "main.py" in listing.text
    assert "python" in listing.text
    assert "print(&#39;hello&#39;)" in listing.text or "print('hello')" in listing.text


def test_create_snippet_with_multiple_files(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Multi-file snippet",
            "tags": "",
            "filename": ["app.py", "requirements.txt"],
            "language": ["python", "plaintext"],
            "content": ["import os", "fastapi"],
        },
    )
    listing = logged_in_client.get("/snippets").text
    assert "app.py" in listing
    assert "requirements.txt" in listing


def _snippet_id_for_title(html: str, title: str) -> str:
    """Zoekt het data-snippet-id horend bij deze titel. Zoekt terug vanaf de titel
    naar de dichtstbijzijnde voorgaande data-snippet-id, i.p.v. voorwaarts (dat zou
    per ongeluk het id van een eerdere kaart kunnen pakken als er meerdere zijn)."""
    marker = f'snippet-card-title-text">{title}<'
    idx = html.index(marker)
    matches = list(re.finditer(r'data-snippet-id="(\d+)"', html[:idx]))
    assert matches, f"Snippet met titel {title!r} niet gevonden"
    return matches[-1].group(1)


def test_edit_snippet(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Origineel", "tags": "", "filename": ["a.py"], "language": ["python"], "content": ["x = 1"]},
    )
    listing = logged_in_client.get("/snippets").text
    snippet_id = _snippet_id_for_title(listing, "Origineel")

    update = logged_in_client.post(
        f"/snippets/{snippet_id}",
        data={
            "title": "Bijgewerkt",
            "tags": "belangrijk",
            "filename": ["b.py"],
            "language": ["python"],
            "content": ["y = 2"],
        },
        follow_redirects=False,
    )
    assert update.status_code == 303

    listing_after = logged_in_client.get("/snippets").text
    assert "Bijgewerkt" in listing_after
    assert "Origineel" not in listing_after
    assert "b.py" in listing_after
    assert "a.py" not in listing_after
    assert "belangrijk" in listing_after


def test_edit_snippet_file_content_from_fullscreen_viewer(logged_in_client):
    """Regressietest voor de aparte content-only route die de fullscreen-viewer gebruikt
    (app/static/js/snippets-list.js) -- moet alleen de code van het aangewezen bestand
    bijwerken, zonder titel/tags/andere bestanden aan te raken."""
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Live-edit-test",
            "tags": "belangrijk",
            "filename": ["a.py"],
            "language": ["python"],
            "content": ["x = 1"],
        },
    )
    listing = logged_in_client.get("/snippets").text
    snippet_id = _snippet_id_for_title(listing, "Live-edit-test")
    idx = listing.index(f'id="snippet-files-{snippet_id}"')
    file_id = re.search(r'data-file-id="(\d+)"', listing[idx:]).group(1)

    response = logged_in_client.post(
        f"/snippets/{snippet_id}/files/{file_id}/content",
        data={"content": "x = 42\nprint(x)"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    listing_after = logged_in_client.get("/snippets").text
    assert "Live-edit-test" in listing_after
    assert "belangrijk" in listing_after
    assert "x = 42" in listing_after


def test_edit_snippet_file_content_requires_login(client):
    response = client.post("/snippets/1/files/1/content", data={"content": "hacked"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_delete_snippet(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Te verwijderen", "tags": "", "filename": ["x.py"], "language": ["python"], "content": [""]},
    )
    listing = logged_in_client.get("/snippets").text
    snippet_id = _snippet_id_for_title(listing, "Te verwijderen")

    response = logged_in_client.post(f"/snippets/{snippet_id}/delete", follow_redirects=False)
    assert response.status_code == 303

    listing_after = logged_in_client.get("/snippets").text
    assert "Te verwijderen" not in listing_after


def test_bulk_delete_snippets(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Bulk een", "tags": "", "filename": ["a.py"], "language": ["python"], "content": ["x = 1"]},
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Bulk twee", "tags": "", "filename": ["b.py"], "language": ["python"], "content": ["y = 2"]},
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Blijft staan", "tags": "", "filename": ["c.py"], "language": ["python"], "content": ["z = 3"]},
    )
    listing = logged_in_client.get("/snippets").text
    id_een = _snippet_id_for_title(listing, "Bulk een")
    id_twee = _snippet_id_for_title(listing, "Bulk twee")

    response = logged_in_client.post(
        "/snippets/bulk-delete", data={"snippet_ids": [id_een, id_twee]}, follow_redirects=False
    )
    assert response.status_code == 303

    listing_after = logged_in_client.get("/snippets").text
    assert "Bulk een" not in listing_after
    assert "Bulk twee" not in listing_after
    assert "Blijft staan" in listing_after


def test_snippet_list_has_select_checkboxes_and_bulk_bar(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Selecteerbaar", "tags": "", "filename": ["a.py"], "language": ["python"], "content": ["x = 1"]},
    )
    page = logged_in_client.get("/snippets").text
    assert 'class="snippet-select" name="snippet_ids"' in page
    assert 'id="snippets-bulk-bar"' in page


def test_filter_snippets_by_tag(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Werksnippet", "tags": "werk", "filename": ["a.py"], "language": ["python"], "content": [""]},
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Privesnippet", "tags": "prive", "filename": ["b.py"], "language": ["python"], "content": [""]},
    )

    filtered = logged_in_client.get("/snippets?tag=werk").text
    assert "Werksnippet" in filtered
    assert "Privesnippet" not in filtered


def test_search_snippets_by_content(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Zoekbare snippet",
            "tags": "",
            "filename": ["a.py"],
            "language": ["python"],
            "content": ["def unique_needle_function(): pass"],
        },
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Andere snippet", "tags": "", "filename": ["b.py"], "language": ["python"], "content": ["x = 1"]},
    )

    results = logged_in_client.get("/snippets?q=unique_needle_function").text
    assert "Zoekbare snippet" in results
    assert "Andere snippet" not in results


def test_search_snippets_by_title(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Uniek titelwoord", "tags": "", "filename": ["a.py"], "language": ["python"], "content": [""]},
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Iets anders", "tags": "", "filename": ["b.py"], "language": ["python"], "content": [""]},
    )

    results = logged_in_client.get("/snippets?q=Uniek titelwoord").text
    assert "Uniek titelwoord" in results
    assert "Iets anders" not in results


def test_search_snippets_by_tag(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "Getagde snippet", "tags": "zeldzametag", "filename": ["a.py"], "language": ["python"], "content": [""]},
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Ongetagde snippet", "tags": "", "filename": ["b.py"], "language": ["python"], "content": [""]},
    )

    results = logged_in_client.get("/snippets?q=zeldzametag").text
    assert "Getagde snippet" in results
    assert "Ongetagde snippet" not in results


def test_collapsed_snippet_ui_present(logged_in_client):
    """Het eerste bestand toont een altijd-zichtbare code-preview op de kaart (ByteStash-
    achtig); bij meerdere bestanden blijven de overige verborgen achter "+ N meer
    bestanden" tot je 'm in het volledige-scherm-paneel opent."""
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Inklaptest",
            "tags": "",
            "filename": ["a.py", "b.py"],
            "language": ["python", "python"],
            "content": ["x = 1", "y = 2"],
        },
    )
    listing = logged_in_client.get("/snippets").text
    snippet_id = _snippet_id_for_title(listing, "Inklaptest")

    files_marker = f'id="snippet-files-{snippet_id}"'
    assert files_marker in listing
    files_start = listing.index(files_marker)
    div_end = listing.index(">", files_start)
    # De container zelf is niet verborgen -- het eerste bestand toont juist een preview.
    assert "hidden" not in listing[files_start:div_end]

    # Het eerste bestand (a.py) is zichtbaar, het tweede (b.py) staat achter "hidden".
    first_file_start = listing.index('data-file-id="', div_end)
    first_file_div_end = listing.index(">", first_file_start)
    assert "hidden" not in listing[first_file_start:first_file_div_end]

    second_file_start = listing.index('data-file-id="', first_file_div_end)
    second_file_div_end = listing.index(">", second_file_start)
    assert "hidden" in listing[second_file_start:second_file_div_end]

    assert "+ 1 meer bestand" in listing


def test_snippet_list_includes_fullscreen_viewer_markup(logged_in_client):
    """De titel opent de code in een los, bijna-volledig-scherm paneel (zie
    snippets-list.js) i.p.v. inline uit te klappen -- dit checkt dat de benodigde
    modal-elementen en de highlight.js-line-numbers-plugin op de pagina staan."""
    page = logged_in_client.get("/snippets").text
    assert 'id="snippet-fullscreen-backdrop"' in page
    assert 'id="snippet-fullscreen-modal"' in page
    assert 'id="snippet-fullscreen-title"' in page
    assert 'id="snippet-fullscreen-body"' in page
    assert "highlightjs-line-numbers.js" in page


def test_snippet_card_shows_description_and_placeholder(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Met beschrijving",
            "description": "Een korte omschrijving",
            "tags": "",
            "filename": ["a.py"],
            "language": ["python"],
            "content": ["x = 1"],
        },
    )
    logged_in_client.post(
        "/snippets",
        data={"title": "Zonder beschrijving", "tags": "", "filename": ["b.py"], "language": ["python"], "content": ["y = 2"]},
    )
    listing = logged_in_client.get("/snippets").text
    assert "Een korte omschrijving" in listing
    assert "Geen beschrijving beschikbaar" in listing


def test_export_snippets_as_json(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={
            "title": "Export test",
            "description": "Beschrijving voor export",
            "tags": "python",
            "filename": ["main.py"],
            "language": ["python"],
            "content": ["print(1)"],
        },
    )
    response = logged_in_client.get("/snippets/export", params={"format": "json"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]

    body = response.json()
    entry = next(s for s in body["snippets"] if s["title"] == "Export test")
    assert entry["description"] == "Beschrijving voor export"
    assert entry["tags"] == ["python"]
    assert entry["files"] == [{"filename": "main.py", "language": "python", "content": "print(1)"}]


def test_export_snippets_as_markdown(logged_in_client):
    logged_in_client.post(
        "/snippets",
        data={"title": "MD export", "tags": "", "filename": ["a.sh"], "language": ["bash"], "content": ["echo hi"]},
    )
    response = logged_in_client.get("/snippets/export", params={"format": "markdown"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "## MD export" in response.text
    assert "```bash" in response.text
    assert "echo hi" in response.text


def test_export_requires_login(client):
    response = client.get("/snippets/export", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_import_snippets_from_json(logged_in_client):
    payload = {
        "exported_at": "2026-01-01T00:00:00",
        "snippets": [
            {
                "title": "Geïmporteerde snippet",
                "description": "Uit een export",
                "tags": ["geimporteerd"],
                "files": [{"filename": "x.py", "language": "python", "content": "x = 1"}],
            }
        ],
    }
    response = logged_in_client.post(
        "/snippets/import",
        files={"import_file": ("export.json", json.dumps(payload), "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "import_success=1" in response.headers["location"]

    listing = logged_in_client.get("/snippets").text
    assert "Geïmporteerde snippet" in listing
    assert "Uit een export" in listing
    assert "geimporteerd" in listing


def test_import_snippets_rejects_invalid_json(logged_in_client):
    response = logged_in_client.post(
        "/snippets/import",
        files={"import_file": ("broken.json", b"dit is geen json", "application/json")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "import_error=" in response.headers["location"]

    listing = logged_in_client.get(response.headers["location"]).text
    assert "Ongeldig of beschadigd JSON-bestand" in listing


def test_import_requires_login(client):
    response = client.post("/snippets/import", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
