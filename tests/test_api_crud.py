from tests.test_api import _auth_headers, _get_api_token


def _h(logged_in_client):
    return _auth_headers(_get_api_token(logged_in_client))


def test_health_requires_token_and_returns_json(client, logged_in_client):
    headers = _h(logged_in_client)
    ok = client.get("/api/v1/health", headers=headers)
    assert ok.status_code == 200 and ok.json() == {"status": "ok", "auth": "ok"}

    anon = client.get("/api/v1/health", headers={})
    assert anon.status_code == 401 and "detail" in anon.json()


def test_no_api_route_redirects_without_token(client):
    for method, path in [
        ("get", "/api/v1/tasks"), ("get", "/api/v1/tasks/1"), ("patch", "/api/v1/tasks/1"),
        ("delete", "/api/v1/tasks/1"), ("get", "/api/v1/notes"), ("get", "/api/v1/snippets"),
        ("get", "/api/v1/kanban"), ("post", "/api/v1/kanban/cards/1/move"), ("get", "/api/v1/nonexistent"),
    ]:
        response = getattr(client, method)(path, headers={"Authorization": "Bearer fout"}, follow_redirects=False)
        assert response.status_code in (401, 404), (method, path, response.status_code)
        assert response.headers["content-type"].startswith("application/json"), (method, path)


def test_task_round_trip(logged_in_client):
    c, h = logged_in_client, _h(logged_in_client)
    created = c.post("/api/v1/tasks", json={"title": "Roundtrip", "tags": "api-test"}, headers=h)
    assert created.status_code == 200
    task_id = created.json()["id"]

    got = c.get(f"/api/v1/tasks/{task_id}", headers=h)
    assert got.status_code == 200 and got.json()["tags"] == ["api-test"]

    listing = c.get("/api/v1/tasks?tag=api-test", headers=h).json()
    assert listing["total"] >= 1 and any(i["id"] == task_id for i in listing["items"])
    assert listing["limit"] == 100 and listing["offset"] == 0

    patched = c.patch(
        f"/api/v1/tasks/{task_id}",
        json={"done": True, "priority": True, "tags": ["a", "b"], "deadline": "2030-01-02"},
        headers=h,
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["done"] is True and body["priority"] is True and body["deadline"] == "2030-01-02"
    assert sorted(body["tags"]) == ["a", "b"]
    assert body["completed_at"] is not None

    assert [i["id"] for i in c.get("/api/v1/tasks?status=done", headers=h).json()["items"]].count(task_id) == 1
    assert task_id not in [i["id"] for i in c.get("/api/v1/tasks?status=open", headers=h).json()["items"]]

    toggled = c.post(f"/api/v1/tasks/{task_id}/toggle-done", headers=h).json()
    assert toggled["done"] is False

    cleared = c.patch(f"/api/v1/tasks/{task_id}", json={"deadline": None}, headers=h).json()
    assert cleared["deadline"] is None

    assert c.patch(f"/api/v1/tasks/{task_id}", json={"title": " "}, headers=h).status_code == 400
    assert c.patch(f"/api/v1/tasks/{task_id}", json={"deadline": "geen-datum"}, headers=h).status_code == 422

    deleted = c.delete(f"/api/v1/tasks/{task_id}", headers=h)
    assert deleted.status_code == 200 and deleted.json() == {"deleted": True, "id": task_id}
    assert c.get(f"/api/v1/tasks/{task_id}", headers=h).status_code == 404


def test_task_archive_and_restore_via_api(logged_in_client):
    from datetime import UTC, datetime, timedelta

    from app.database import SessionLocal
    from app.models.task import Task

    c, h = logged_in_client, _h(logged_in_client)
    task_id = c.post("/api/v1/tasks", json={"title": "Archief-API"}, headers=h).json()["id"]
    c.post(f"/api/v1/tasks/{task_id}/toggle-done", headers=h)
    with SessionLocal() as db:
        db.get(Task, task_id).completed_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=12)
        db.commit()

    archived = c.get("/api/v1/tasks?status=archived", headers=h).json()["items"]
    assert any(i["id"] == task_id and i["archived"] for i in archived)

    restored = c.post(f"/api/v1/tasks/{task_id}/restore", headers=h).json()
    assert restored["archived"] is False and restored["done"] is False
    c.delete(f"/api/v1/tasks/{task_id}", headers=h)


def test_task_list_pagination_and_validation(logged_in_client):
    c, h = logged_in_client, _h(logged_in_client)
    ids = [c.post("/api/v1/tasks", json={"title": f"Pagina {i}"}, headers=h).json()["id"] for i in range(3)]
    page = c.get("/api/v1/tasks?limit=2&offset=0", headers=h).json()
    assert len(page["items"]) == 2 and page["total"] >= 3
    assert c.get("/api/v1/tasks?limit=0", headers=h).status_code == 422
    assert c.get("/api/v1/tasks?status=raar", headers=h).status_code == 422
    for i in ids:
        c.delete(f"/api/v1/tasks/{i}", headers=h)


def test_note_crud(logged_in_client):
    c, h = logged_in_client, _h(logged_in_client)
    note_id = c.post("/api/v1/notes", json={"title": "API-notitie", "content": "<p>x</p>"}, headers=h).json()["id"]
    assert c.get(f"/api/v1/notes/{note_id}", headers=h).json()["title"] == "API-notitie"

    patched = c.patch(
        f"/api/v1/notes/{note_id}",
        json={"content": "<p>nieuw</p><script>x</script>", "is_temp": True, "tags": "n1"},
        headers=h,
    ).json()
    assert "<script>" not in patched["content"] and patched["is_temp"] is True and patched["tags"] == ["n1"]

    assert any(i["id"] == note_id for i in c.get("/api/v1/notes?is_temp=true", headers=h).json()["items"])
    assert c.delete(f"/api/v1/notes/{note_id}", headers=h).json() == {"deleted": True, "id": note_id}
    assert c.get(f"/api/v1/notes/{note_id}", headers=h).status_code == 404


def test_snippet_crud_includes_files(logged_in_client):
    c, h = logged_in_client, _h(logged_in_client)
    snippet_id = c.post(
        "/api/v1/snippets",
        json={"title": "API-snippet", "files": [{"filename": "a.py", "language": "python", "content": "print(1)"}]},
        headers=h,
    ).json()["id"]
    got = c.get(f"/api/v1/snippets/{snippet_id}", headers=h).json()
    assert got["files"][0]["content"] == "print(1)"

    patched = c.patch(f"/api/v1/snippets/{snippet_id}", json={"title": "Nieuw", "tags": "s1"}, headers=h).json()
    assert patched["title"] == "Nieuw" and patched["tags"] == ["s1"] and len(patched["files"]) == 1

    assert any(i["id"] == snippet_id for i in c.get("/api/v1/snippets?tag=s1", headers=h).json()["items"])
    assert c.delete(f"/api/v1/snippets/{snippet_id}", headers=h).status_code == 200
    assert c.get(f"/api/v1/snippets/{snippet_id}", headers=h).status_code == 404


def test_kanban_board_cards_move_and_swimlanes(logged_in_client):
    c, h = logged_in_client, _h(logged_in_client)
    lane = c.post("/api/v1/kanban/swimlanes", json={"name": "API-lane"}, headers=h).json()
    columns = lane["columns"]

    card = c.post(
        "/api/v1/kanban/cards",
        json={"title": "API-kaart", "description": "- [ ] stap", "swimlane_id": lane["id"], "column_id": columns[0]["id"]},
        headers=h,
    ).json()

    board = c.get("/api/v1/kanban", headers=h).json()
    lane_json = next(s for s in board["swimlanes"] if s["id"] == lane["id"])
    assert any(card["id"] == k["id"] for col in lane_json["columns"] for k in col["cards"])

    assert c.get(f"/api/v1/kanban/cards?swimlane_id={lane['id']}", headers=h).json()["total"] == 1

    moved = c.post(
        f"/api/v1/kanban/cards/{card['id']}/move",
        json={"swimlane_id": lane["id"], "column_id": columns[2]["id"], "position": 0},
        headers=h,
    ).json()
    assert moved["column_id"] == columns[2]["id"]
    assert c.post(
        f"/api/v1/kanban/cards/{card['id']}/move",
        json={"swimlane_id": lane["id"], "column_id": 999999, "position": 0},
        headers=h,
    ).status_code == 404

    toggled = c.post(f"/api/v1/kanban/cards/{card['id']}/checklist-toggle", json={"line_index": 0}, headers=h).json()
    assert toggled["checklist"] == {"done": 1, "total": 1}

    patched = c.patch(
        f"/api/v1/kanban/cards/{card['id']}", json={"title": "Nieuw", "color": "#ff0000", "tags": "k1"}, headers=h
    ).json()
    assert patched["title"] == "Nieuw" and patched["color"] == "#ff0000" and patched["tags"] == ["k1"]
    assert c.patch(f"/api/v1/kanban/cards/{card['id']}", json={"color": None}, headers=h).json()["color"] is None

    renamed = c.patch(f"/api/v1/kanban/swimlanes/{lane['id']}", json={"name": "API-lane 2"}, headers=h).json()
    assert renamed["name"] == "API-lane 2"
    assert any(s["id"] == lane["id"] for s in c.get("/api/v1/kanban/swimlanes", headers=h).json()["items"])

    assert c.delete(f"/api/v1/kanban/cards/{card['id']}", headers=h).json() == {"deleted": True, "id": card["id"]}
    assert c.delete(f"/api/v1/kanban/swimlanes/{lane['id']}", headers=h).json()["deleted"] is True
    assert c.get(f"/api/v1/kanban/cards/{card['id']}", headers=h).status_code == 404
