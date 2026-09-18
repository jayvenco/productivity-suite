import re


def _get_api_token(logged_in_client) -> str:
    response = logged_in_client.post("/account/api-token/generate")
    match = re.search(r'<code style="user-select:all">([^<]+)</code>', response.text)
    assert match, "Geen nieuw token gevonden in de account-pagina"
    return match.group(1)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_api_requires_token(client):
    response = client.post("/api/v1/tasks", json={"title": "Zonder token"})
    assert response.status_code == 401


def test_api_rejects_invalid_token(client):
    response = client.post(
        "/api/v1/tasks", json={"title": "Fout token"}, headers=_auth_headers("onbestaand-token")
    )
    assert response.status_code == 401


def test_generate_and_use_api_token(logged_in_client):
    token = _get_api_token(logged_in_client)

    response = logged_in_client.post(
        "/api/v1/tasks", json={"title": "Via API"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Via API"

    listing = logged_in_client.get("/tasks").text
    assert "Via API" in listing


def test_revoking_token_blocks_further_use(logged_in_client):
    token = _get_api_token(logged_in_client)
    logged_in_client.post("/account/api-token/revoke")

    response = logged_in_client.post(
        "/api/v1/tasks", json={"title": "Na intrekken"}, headers=_auth_headers(token)
    )
    assert response.status_code == 401


def test_regenerating_token_invalidates_previous_one(logged_in_client):
    old_token = _get_api_token(logged_in_client)
    new_token = _get_api_token(logged_in_client)
    assert old_token != new_token

    old_response = logged_in_client.post(
        "/api/v1/tasks", json={"title": "Met oud token"}, headers=_auth_headers(old_token)
    )
    assert old_response.status_code == 401

    new_response = logged_in_client.post(
        "/api/v1/tasks", json={"title": "Met nieuw token"}, headers=_auth_headers(new_token)
    )
    assert new_response.status_code == 200


def test_api_create_task_with_tags_and_deadline(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/tasks",
        json={"title": "Rapport", "description": "Kwartaalrapport af", "deadline": "2026-12-01", "tags": "werk, q4"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deadline"] == "2026-12-01"
    assert sorted(body["tags"]) == ["q4", "werk"]


def test_api_create_task_requires_title(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post("/api/v1/tasks", json={"title": "   "}, headers=_auth_headers(token))
    assert response.status_code == 400


def test_api_create_kanban_card_uses_default_cell(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/kanban/cards", json={"title": "Kaart via API", "tags": "agent"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Kaart via API"
    assert body["swimlane_id"] is not None
    assert body["column_id"] is not None

    board_html = logged_in_client.get("/kanban").text
    assert "Kaart via API" in board_html


def test_api_create_kanban_card_rejects_foreign_cell(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/kanban/cards",
        json={"title": "x", "swimlane_id": 999999, "column_id": 999999},
        headers=_auth_headers(token),
    )
    assert response.status_code == 404


def test_api_create_note(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/notes",
        json={"title": "Notitie via API", "content": "<p>Hallo</p><script>alert(1)</script>", "tags": "agent"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert "<script>" not in body["content"]
    assert "Hallo" in body["content"]

    listing = logged_in_client.get("/notes").text
    assert "Notitie via API" in listing


def test_api_create_snippet_with_multiple_files(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/snippets",
        json={
            "title": "Snippet via API",
            "tags": "agent",
            "files": [
                {"filename": "main.py", "language": "python", "content": "print('hi')"},
                {"filename": "requirements.txt", "language": "plaintext", "content": "fastapi"},
            ],
        },
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["files"]) == 2

    listing = logged_in_client.get("/snippets").text
    assert "Snippet via API" in listing


def test_api_create_snippet_requires_at_least_one_file(logged_in_client):
    token = _get_api_token(logged_in_client)
    response = logged_in_client.post(
        "/api/v1/snippets", json={"title": "Leeg", "files": []}, headers=_auth_headers(token)
    )
    assert response.status_code == 422
