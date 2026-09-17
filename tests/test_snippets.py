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
    match = re.search(rf'/snippets/(\d+)/edit"[^>]*>{re.escape(title)}<', html)
    assert match, f"Snippet met titel {title!r} niet gevonden"
    return match.group(1)


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
