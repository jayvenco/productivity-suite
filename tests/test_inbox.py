import re

from app.database import SessionLocal
from app.models.inbox import InboxItem
from app.models.kanban import KanbanCard
from app.models.note import Note
from app.models.task import Task
from tests.test_api import _auth_headers, _get_api_token


def _add(client, text):
    return client.post("/inbox", data={"text": text}, headers={"X-Requested-With": "fetch"})


def _item_id(client, text):
    html = client.get("/inbox").text
    idx = html.index(text)
    return re.search(r'formaction="/inbox/(\d+)/to-note"', html[idx:]).group(1)


def test_inbox_requires_login(client):
    assert client.get("/inbox", follow_redirects=False).status_code == 303


def test_add_via_fetch_returns_count_and_empty_is_rejected(logged_in_client):
    before = logged_in_client.get("/inbox/count").json()["count"]
    r = _add(logged_in_client, "Snel idee voor later")
    assert r.status_code == 200 and r.json()["count"] == before + 1
    assert _add(logged_in_client, "   ").status_code == 400
    assert "Snel idee voor later" in logged_in_client.get("/inbox").text
    logged_in_client.post(f"/inbox/{_item_id(logged_in_client, 'Snel idee voor later')}/delete")


def test_convert_to_task_note_and_card_removes_item(logged_in_client):
    _add(logged_in_client, "Taak-titel\nmet beschrijving")
    task = logged_in_client.post(
        f"/inbox/{_item_id(logged_in_client, 'Taak-titel')}/to-task",
        data={"deadline": "2031-03-04", "tags": "inboxtag"}, follow_redirects=False,
    )
    assert task.status_code == 303 and "/tasks/" in task.headers["location"]
    with SessionLocal() as db:
        created = db.query(Task).filter(Task.title == "Taak-titel").one()
        assert created.description == "met beschrijving" and str(created.deadline) == "2031-03-04"
        assert [t.name for t in created.tags] == ["inboxtag"]
        db.delete(created)
        db.commit()
    assert "Taak-titel" not in logged_in_client.get("/inbox").text

    _add(logged_in_client, "Notitie-titel\nregel 5 & 6\nregel twee")
    note = logged_in_client.post(f"/inbox/{_item_id(logged_in_client, 'Notitie-titel')}/to-note", follow_redirects=False)
    assert note.status_code == 303 and "/edit" in note.headers["location"]
    with SessionLocal() as db:
        created = db.query(Note).filter(Note.title == "Notitie-titel").one()
        assert "<p>regel 5 &amp; 6</p>" in created.content and "<p>regel twee</p>" in created.content
        db.delete(created)
        db.commit()

    _add(logged_in_client, "Kaart-titel")
    card = logged_in_client.post(f"/inbox/{_item_id(logged_in_client, 'Kaart-titel')}/to-card", follow_redirects=False)
    assert card.status_code == 303 and card.headers["location"] == "/kanban"
    with SessionLocal() as db:
        created = db.query(KanbanCard).filter(KanbanCard.title == "Kaart-titel").one()
        db.delete(created)
        db.commit()
        assert db.query(InboxItem).filter(InboxItem.text == "Kaart-titel").count() == 0


def test_inbox_nav_and_quick_capture_markup(logged_in_client):
    page = logged_in_client.get("/tasks").text
    assert 'href="/inbox"' in page and 'id="inbox-quick-btn"' in page and 'id="inbox-capture"' in page


def test_inbox_api_roundtrip_and_convert(logged_in_client):
    h = _auth_headers(_get_api_token(logged_in_client))
    c = logged_in_client
    item = c.post("/api/v1/inbox", json={"text": "API-inbox titel\nrest"}, headers=h).json()
    assert item["title"] == "API-inbox titel" and item["rest"] == "rest"
    assert c.post("/api/v1/inbox", json={"text": " "}, headers=h).status_code == 400
    assert any(i["id"] == item["id"] for i in c.get("/api/v1/inbox", headers=h).json()["items"])
    assert c.post(f"/api/v1/inbox/{item['id']}/convert", json={"to": "nonsens"}, headers=h).status_code == 422

    done = c.post(f"/api/v1/inbox/{item['id']}/convert", json={"to": "task", "deadline": "2031-01-02", "tags": "ai"}, headers=h)
    assert done.status_code == 200 and done.json()["type"] == "task" and done.json()["deadline"] == "2031-01-02"
    assert c.get(f"/api/v1/inbox/{item['id']}", headers=h).status_code == 404
    c.delete(f"/api/v1/tasks/{done.json()['id']}", headers=h)

    other = c.post("/api/v1/inbox", json={"text": "Weg ermee"}, headers=h).json()
    assert c.delete(f"/api/v1/inbox/{other['id']}", headers=h).json() == {"deleted": True, "id": other["id"]}
