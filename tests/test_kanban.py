import re


def _first_ids(html: str):
    column_id = re.search(r'data-column-id="(\d+)"', html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', html).group(1)
    return column_id, swimlane_id


def _swimlane_id_for_name(html: str, name: str) -> str:
    """Zoekt het data-swimlane-toggle-id horend bij deze swimlane-naam. Zoekt terug
    vanaf de naam naar de dichtstbijzijnde voorgaande data-swimlane-toggle, i.p.v.
    voorwaarts -- anders kan een niet-greedy .*? per ongeluk over een hele
    swimlane-sectie heen springen naar een latere naam."""
    marker = f'swimlane-toggle-arrow">▾</span> {name}'
    idx = html.index(marker)
    matches = list(re.finditer(r'data-swimlane-toggle="(\d+)"', html[:idx]))
    assert matches, f"Swimlane met naam {name!r} niet gevonden"
    return matches[-1].group(1)


def _card_id_for_title(html: str, title: str) -> str:
    """Zoekt het data-card-id van de kaart met deze titel (het board bevat kaarten
    uit eerdere tests in dezelfde sessie, dus de eerste data-card-id is niet altijd
    de juiste)."""
    match = re.search(rf'data-card-id="(\d+)"[^>]*>\s*<div class="card-title">{re.escape(title)}</div>', html)
    assert match, f"Kaart met titel {title!r} niet gevonden"
    return match.group(1)


def test_new_swimlane_gets_distinct_column_color(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    algemeen_hue = re.search(r"border-top: 3px solid hsl\((\d+),", board_html).group(1)

    logged_in_client.post("/kanban/swimlanes", data={"name": "Kleurentest lane"})
    board_html_after = logged_in_client.get("/kanban").text

    hues = re.findall(r"border-top: 3px solid hsl\((\d+),", board_html_after)
    assert len(set(hues)) >= 2, "Nieuwe swimlane heeft geen andere kolomkleur gekregen"
    assert algemeen_hue in hues


def test_board_has_seeded_columns_and_swimlane(logged_in_client):
    response = logged_in_client.get("/kanban")
    assert response.status_code == 200
    assert "Backlog" in response.text
    assert "Todo" in response.text
    assert "Algemeen" in response.text
    # Backlog hoort vóór Todo te staan (eerste kolom van de Algemeen-swimlane).
    assert response.text.index("Backlog") < response.text.index(">Todo<")


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


def test_new_swimlane_gets_its_own_default_columns(logged_in_client):
    before = logged_in_client.get("/kanban").text
    todo_count_before = before.count(">Todo<")

    logged_in_client.post("/kanban/swimlanes", data={"name": "Design"})

    after = logged_in_client.get("/kanban").text
    assert after.count(">Todo<") == todo_count_before + 1
    assert "Design" in after


def test_add_custom_column_to_swimlane(logged_in_client):
    logged_in_client.post("/kanban/swimlanes", data={"name": "Marketing"})
    board_html = logged_in_client.get("/kanban").text
    swimlane_id = _swimlane_id_for_name(board_html, "Marketing")

    response = logged_in_client.post(
        f"/kanban/swimlanes/{swimlane_id}/columns", data={"name": "Review"}, follow_redirects=False
    )
    assert response.status_code == 303

    board_html_after = logged_in_client.get("/kanban").text
    assert board_html_after.count(">Review<") == 1


def test_cannot_create_card_with_column_from_other_swimlane(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    algemeen_column_id, _ = _first_ids(board_html)

    logged_in_client.post("/kanban/swimlanes", data={"name": "Andere lane"})
    board_html_after = logged_in_client.get("/kanban").text
    other_swimlane_id = _swimlane_id_for_name(board_html_after, "Andere lane")

    response = logged_in_client.post(
        "/kanban/cards",
        data={
            "column_id": algemeen_column_id,
            "swimlane_id": other_swimlane_id,
            "title": "Mag niet",
            "description": "",
        },
    )
    assert response.status_code == 404


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
