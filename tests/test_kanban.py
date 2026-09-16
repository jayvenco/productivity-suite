import re


def _first_ids(html: str):
    column_id = re.search(r'data-column-id="(\d+)"', html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', html).group(1)
    return column_id, swimlane_id


def test_board_has_seeded_columns_and_swimlane(logged_in_client):
    response = logged_in_client.get("/kanban")
    assert response.status_code == 200
    assert "Todo" in response.text
    assert "Algemeen" in response.text


def test_create_card_with_checklist_and_toggle(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)

    create = logged_in_client.post(
        "/kanban/cards",
        data={
            "column_id": column_id,
            "swimlane_id": swimlane_id,
            "title": "Boodschappen",
            "description": "- [ ] Melk\n- [ ] Brood",
            "tags": "prive",
        },
        follow_redirects=False,
    )
    assert create.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Boodschappen" in board_html
    card_id = re.search(r'data-card-id="(\d+)"', board_html).group(1)
    assert 'data-line-index="0"' in board_html

    toggle = logged_in_client.post(f"/kanban/cards/{card_id}/checklist-toggle", data={"line_index": "0"})
    assert toggle.status_code == 200

    board_html_after = logged_in_client.get("/kanban").text
    assert 'checklist-item done' in board_html_after


def test_create_swimlane(logged_in_client):
    response = logged_in_client.post("/kanban/swimlanes", data={"name": "Werk"}, follow_redirects=False)
    assert response.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Werk" in board_html
