import re

from app.database import SessionLocal
from app.models.kanban import KanbanCard
from app.services.richtext import (
    html_checklist_progress,
    looks_like_html,
    plain_text,
    sanitize_note_html,
    sanitize_rich,
    split_rich,
    toggle_html_checklist,
)
from tests.test_api import _auth_headers, _get_api_token

CHECK_HTML = (
    '<ul class="rt-checklist"><li data-checked="0">een</li><li data-checked="1">twee</li>'
    '<li data-checked="0">drie</li></ul>'
)


def test_checklist_markup_survives_sanitizer_and_scripts_do_not():
    cleaned = sanitize_note_html(CHECK_HTML + "<script>x</script><p onclick='x()'>ok</p>")
    assert 'class="rt-checklist"' in cleaned and cleaned.count("data-checked") == 3
    assert "<script>" not in cleaned and "onclick" not in cleaned


def test_html_checklist_helpers():
    assert html_checklist_progress(CHECK_HTML) == (1, 3)
    flipped = toggle_html_checklist(CHECK_HTML, 0)
    assert html_checklist_progress(flipped) == (2, 3)
    assert html_checklist_progress(toggle_html_checklist(flipped, 1)) == (1, 3)
    assert toggle_html_checklist("geen html", 0) == "geen html"


def test_plain_text_and_detection():
    assert looks_like_html("<p>x</p>") and not looks_like_html("gewone tekst met 5 < 6")
    assert plain_text("<p>Hallo <b>wereld</b></p><ul><li>a</li><li>b</li></ul>") == "Hallo wereld a b"
    assert plain_text("platte tekst blijft") == "platte tekst blijft"
    assert sanitize_rich("platte tekst") == "platte tekst"


def test_split_rich_for_html_and_plain():
    assert split_rich("Titel\nrest\nmeer") == ("Titel", "rest\nmeer")
    title, rest = split_rich("<h2>Kop</h2><p>tekst</p>")
    assert title == "Kop" and rest == "<p>tekst</p>"
    title, rest = split_rich("<p>Titel<br>onder</p><p>nog</p>")
    assert title == "Titel" and "onder" in rest and "nog" in rest


def test_editor_is_mounted_on_notes_tasks_cards_and_inbox(logged_in_client):
    assert 'name="content" id="content" data-rich-editor' in logged_in_client.get("/notes/new").text
    assert 'name="description" data-rich-editor' in logged_in_client.get("/tasks/new").text
    assert "data-rich-editor" in logged_in_client.get("/inbox").text
    assert 'id="inbox-capture-text" rows="5" data-rich-editor' in logged_in_client.get("/inbox").text
    assert "js/rich-editor.js" in logged_in_client.get("/tasks").text
    assert "md-toolbar" not in logged_in_client.get("/kanban").text


def test_task_description_html_is_sanitized_and_preview_is_plain(logged_in_client):
    logged_in_client.post(
        "/tasks",
        data={"title": "Rich-taak", "description": "<p>Tekst <b>vet</b></p><script>x</script>" + CHECK_HTML, "deadline": "", "tags": ""},
    )
    page = logged_in_client.get("/tasks").text
    card = page[page.index("Rich-taak"): page.index("Rich-taak") + 900]
    assert "task-card-preview" in card and "<b>" not in card.split("task-card-preview")[1][:120]
    with SessionLocal() as db:
        from app.models.task import Task

        task = db.query(Task).filter(Task.title == "Rich-taak").one()
        assert "<script>" not in task.description and "data-checked" in task.description
        db.delete(task)
        db.commit()


def test_kanban_card_html_description_renders_and_checklist_toggles(logged_in_client):
    board = logged_in_client.get("/kanban").text
    column_id = re.search(r'data-column-id="(\d+)" data-swimlane-id="(\d+)"', board)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id.group(1), "swimlane_id": column_id.group(2), "title": "Rich-kaart",
              "description": CHECK_HTML, "tags": ""},
    )
    with SessionLocal() as db:
        card = db.query(KanbanCard).filter(KanbanCard.title == "Rich-kaart").one()
        card_id = card.id
    page = logged_in_client.get("/kanban").text
    assert f'<div class="rich-html" data-card-id="{card_id}">' in page

    r = logged_in_client.post(f"/kanban/cards/{card_id}/checklist-toggle", data={"item_index": "0"})
    assert r.status_code == 200
    with SessionLocal() as db:
        assert html_checklist_progress(db.get(KanbanCard, card_id).description) == (2, 3)
    assert logged_in_client.post(f"/kanban/cards/{card_id}/checklist-toggle", data={}).status_code == 422
    logged_in_client.post(f"/kanban/cards/{card_id}/delete")


def test_legacy_markdown_card_still_uses_classic_checklist(logged_in_client):
    board = logged_in_client.get("/kanban").text
    ids = re.search(r'data-column-id="(\d+)" data-swimlane-id="(\d+)"', board)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": ids.group(1), "swimlane_id": ids.group(2), "title": "Oude-kaart",
              "description": "- [ ] oud item", "tags": ""},
    )
    page = logged_in_client.get("/kanban").text
    assert 'class="checklist-item' in page and 'data-line-index="0"' in page
    with SessionLocal() as db:
        card = db.query(KanbanCard).filter(KanbanCard.title == "Oude-kaart").one()
        db.delete(card)
        db.commit()


def test_inbox_html_item_converts_with_html_description(logged_in_client):
    logged_in_client.post("/inbox", data={"text": "<p>Rich titel</p><p>beschrijving <b>vet</b></p>" + CHECK_HTML},
                          headers={"X-Requested-With": "fetch"})
    html = logged_in_client.get("/inbox").text
    assert '<div class="rich-html">' in html
    item_id = re.search(r'formaction="/inbox/(\d+)/to-task"', html[html.index("Rich titel"):]).group(1)
    r = logged_in_client.post(f"/inbox/{item_id}/to-task", follow_redirects=False)
    assert r.status_code == 303
    with SessionLocal() as db:
        from app.models.task import Task

        task = db.query(Task).filter(Task.title == "Rich titel").one()
        assert "<b>vet</b>" in task.description and html_checklist_progress(task.description) == (1, 3)
        db.delete(task)
        db.commit()


def test_api_card_checklist_progress_for_html(logged_in_client):
    h = _auth_headers(_get_api_token(logged_in_client))
    card = logged_in_client.post("/api/v1/kanban/cards", json={"title": "API-rich", "description": CHECK_HTML}, headers=h).json()
    got = logged_in_client.get(f"/api/v1/kanban/cards/{card['id']}", headers=h).json()
    assert got["checklist"] == {"done": 1, "total": 3}
    toggled = logged_in_client.post(f"/api/v1/kanban/cards/{card['id']}/checklist-toggle", json={"item_index": 2}, headers=h).json()
    assert toggled["checklist"] == {"done": 2, "total": 3}
    logged_in_client.delete(f"/api/v1/kanban/cards/{card['id']}", headers=h)


def test_split_rich_handles_bare_first_line_followed_by_block():
    """Chrome maakt 'titel<div>rest</div>' als de eerste regel niet in een <p> staat."""
    title, rest = split_rich("Idee voor de website<div>met een tweede regel</div>")
    assert title == "Idee voor de website" and rest == "<div>met een tweede regel</div>"
    assert split_rich("Alleen een titel")[0] == "Alleen een titel"
    assert split_rich("Tekst met <b>vet</b> erin")[0] == "Tekst met vet erin"
