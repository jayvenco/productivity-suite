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
    logged_in_client.post(
        "/snippets",
        data={"title": "Inklaptest", "tags": "", "filename": ["a.py"], "language": ["python"], "content": ["x = 1"]},
    )
    listing = logged_in_client.get("/snippets").text
    snippet_id = _snippet_id_for_title(listing, "Inklaptest")

    # De code-inhoud moet standaard verborgen zijn (achter een hidden container).
    files_marker = f'id="snippet-files-{snippet_id}"'
    assert files_marker in listing
    files_start = listing.index(files_marker)
    # De 'hidden'-attribuut moet vlak vóór de afsluitende '>' van deze div staan.
    div_end = listing.index(">", files_start)
    assert "hidden" in listing[files_start:div_end]


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
