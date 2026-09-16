import re


def _first_ids(html: str):
    column_id = re.search(r'data-column-id="(\d+)"', html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', html).group(1)
    return column_id, swimlane_id


def _card_id_for_title(html: str, title: str) -> str:
    """Zoekt het data-card-id van de kaart met deze titel (het board bevat kaarten
    uit eerdere tests in dezelfde sessie, dus de eerste data-card-id is niet altijd
    de juiste)."""
    match = re.search(rf'data-card-id="(\d+)"[^>]*>\s*<div class="card-title">{re.escape(title)}</div>', html)
    assert match, f"Kaart met titel {title!r} niet gevonden"
    return match.group(1)


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
    card_id = _card_id_for_title(board_html, "Boodschappen")
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


def test_edit_card_title_description_tags_and_color(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)

    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Origineel", "description": ""},
    )
    board_html = logged_in_client.get("/kanban").text
    card_id = _card_id_for_title(board_html, "Origineel")

    update = logged_in_client.post(
        f"/kanban/cards/{card_id}",
        data={
            "title": "Bijgewerkt",
            "description": "Nieuwe tekst",
            "tags": "belangrijk",
            "color": "#ff8800",
        },
        follow_redirects=False,
    )
    assert update.status_code == 303

    board_html_after = logged_in_client.get("/kanban").text
    assert "Bijgewerkt" in board_html_after
    assert "Origineel" not in board_html_after
    assert "#ff8800" in board_html_after
    assert "belangrijk" in board_html_after


def test_clear_card_color(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)

    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Kleurtest", "description": ""},
    )
    board_html = logged_in_client.get("/kanban").text
    card_id = _card_id_for_title(board_html, "Kleurtest")

    logged_in_client.post(
        f"/kanban/cards/{card_id}",
        data={"title": "Kleurtest", "description": "", "color": "#123456"},
    )
    with_color = logged_in_client.get("/kanban").text
    assert "#123456" in with_color

    logged_in_client.post(
        f"/kanban/cards/{card_id}",
        data={"title": "Kleurtest", "description": "", "color": "#123456", "clear_color": "true"},
    )
    without_color = logged_in_client.get("/kanban").text
    assert "#123456" not in without_color
