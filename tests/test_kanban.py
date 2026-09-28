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


def test_default_cell_returns_first_swimlane_and_column(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)

    response = logged_in_client.get("/kanban/default-cell")
    assert response.status_code == 200
    assert response.json() == {"swimlane_id": int(swimlane_id), "column_id": int(column_id)}


def test_default_cell_requires_login(client):
    response = client.get("/kanban/default-cell", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def _card_id_for_title(html: str, title: str) -> str:
    """Zoekt het data-card-id van de kaart met deze titel (het board bevat kaarten
    uit eerdere tests in dezelfde sessie, dus de eerste data-card-id is niet altijd
    de juiste)."""
    match = re.search(rf'data-card-id="(\d+)"[^>]*>\s*<div class="card-title">{re.escape(title)}</div>', html)
    assert match, f"Kaart met titel {title!r} niet gevonden"
    return match.group(1)


def test_new_swimlane_gets_distinct_column_color(logged_in_client):
    """Kolommen zelf zijn een egaal vlak (geen kleurtint meer); de swimlane-kleur
    is nog wel zichtbaar via het kleine bolletje in de kolomkop en de
    linkerrand van de swimlane-titel."""
    board_html = logged_in_client.get("/kanban").text
    algemeen_hue = re.search(r"border-left: 3px solid hsl\((\d+),", board_html).group(1)

    logged_in_client.post("/kanban/swimlanes", data={"name": "Kleurentest lane"})
    board_html_after = logged_in_client.get("/kanban").text

    hues = re.findall(r"border-left: 3px solid hsl\((\d+),", board_html_after)
    assert len(set(hues)) >= 2, "Nieuwe swimlane heeft geen andere kleur gekregen"
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


def test_add_task_as_card_links_and_copies_fields(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Auto laten wassen", "description": "zaterdag inplannen", "deadline": "", "tags": "auto"}
    )
    tasks_html = logged_in_client.get("/tasks").text
    idx = tasks_html.rindex("Auto laten wassen")
    task_id = re.findall(r'data-href="/tasks/(\d+)/edit"', tasks_html[:idx])[-1]

    board_html = logged_in_client.get("/kanban").text
    assert f'<option value="{task_id}">Auto laten wassen</option>' in board_html
    column_id, swimlane_id = _first_ids(board_html)

    response = logged_in_client.post(
        "/kanban/cards/from-task",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "task_id": task_id},
        follow_redirects=False,
    )
    assert response.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Auto laten wassen" in board_html
    assert f'href="/tasks/{task_id}/edit"' in board_html
    # Tags zijn niet zichtbaar op het bord zelf (zie architectuurnotitie "Tags weg uit de
    # overzichten"), maar wel meegekopieerd naar het (verborgen) bewerkformulier van de kaart.
    assert 'name="tags" placeholder="Tags (komma-gescheiden)" value="auto"' in board_html
    # De taak staat niet meer in de keuzelijst, want die is al aan een kaart gekoppeld.
    assert f'<option value="{task_id}">Auto laten wassen</option>' not in board_html


def test_add_task_as_card_requires_existing_task(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)
    response = logged_in_client.post(
        "/kanban/cards/from-task",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "task_id": 999999},
    )
    assert response.status_code == 404


def test_done_tasks_are_not_offered_as_cards(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Al afgerond", "description": "", "deadline": "", "tags": ""})
    tasks_html = logged_in_client.get("/tasks").text
    match = re.search(r'data-href="/tasks/(\d+)/edit">[\s\S]*?Al afgerond', tasks_html)
    assert match, "Taak niet gevonden"
    task_id = match.group(1)
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")

    board_html = logged_in_client.get("/kanban").text
    assert f'<option value="{task_id}">Al afgerond</option>' not in board_html

    # Opruimen: andere tests in dezelfde testrun delen deze database en doen soms brede
    # "task-card-done" not in ...-checks -- een hier achtergelaten afgeronde taak zou die
    # tests laten falen, dus meteen weer opruimen i.p.v. alleen terugzetten naar "todo".
    logged_in_client.post(f"/tasks/{task_id}/delete")


def test_create_swimlane(logged_in_client):
    response = logged_in_client.post("/kanban/swimlanes", data={"name": "Werk"}, follow_redirects=False)
    assert response.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Werk" in board_html


def test_rename_swimlane(logged_in_client):
    logged_in_client.post("/kanban/swimlanes", data={"name": "Hernoem-mij"})
    board_html = logged_in_client.get("/kanban").text
    swimlane_id = _swimlane_id_for_name(board_html, "Hernoem-mij")

    response = logged_in_client.post(
        f"/kanban/swimlanes/{swimlane_id}/rename", data={"name": "Hernoemd"}, follow_redirects=False
    )
    assert response.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Hernoemd" in board_html
    assert "Hernoem-mij" not in board_html


def test_delete_swimlane_removes_its_cards(logged_in_client):
    logged_in_client.post("/kanban/swimlanes", data={"name": "Weg-te-gooien"})
    board_html = logged_in_client.get("/kanban").text
    swimlane_id = _swimlane_id_for_name(board_html, "Weg-te-gooien")
    column_id = re.search(
        rf'data-column-id="(\d+)" data-swimlane-id="{swimlane_id}"', board_html
    ).group(1)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Kaart in te verwijderen lane", "description": "", "tags": ""},
    )

    response = logged_in_client.post(f"/kanban/swimlanes/{swimlane_id}/delete", follow_redirects=False)
    assert response.status_code == 303

    board_html = logged_in_client.get("/kanban").text
    assert "Weg-te-gooien" not in board_html
    assert "Kaart in te verwijderen lane" not in board_html


def test_cannot_delete_last_swimlane(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    _, swimlane_id = _first_ids(board_html)
    swimlane_count = board_html.count("swimlane-toggle=")
    if swimlane_count > 1:
        # Deze testrun heeft (door eerdere tests) meer dan één swimlane -- verwijder de
        # rest tot er nog maar één over is, zodat deze test z'n eigen randgeval test.
        for sid in re.findall(r'data-swimlane-toggle="(\d+)"', board_html)[1:]:
            logged_in_client.post(f"/kanban/swimlanes/{sid}/delete")

    response = logged_in_client.post(f"/kanban/swimlanes/{swimlane_id}/delete")
    assert response.status_code == 400


def test_delete_swimlane_requires_login(client):
    response = client.post("/kanban/swimlanes/1/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_bare_url_in_card_description_is_auto_linked(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)

    logged_in_client.post(
        "/kanban/cards",
        data={
            "column_id": column_id,
            "swimlane_id": swimlane_id,
            "title": "Linktest kaart",
            "description": "Zie www.mondschoon.nl voor meer info",
        },
    )
    board_html_after = logged_in_client.get("/kanban").text
    assert '<a href="http://www.mondschoon.nl"' in board_html_after


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


def test_set_and_clear_swimlane_color(logged_in_client):
    logged_in_client.post("/kanban/swimlanes", data={"name": "Kleurkeuze lane"})
    board_html = logged_in_client.get("/kanban").text
    swimlane_id = _swimlane_id_for_name(board_html, "Kleurkeuze lane")

    logged_in_client.post(f"/kanban/swimlanes/{swimlane_id}/color", data={"color": "#00ff99"})
    with_color = logged_in_client.get("/kanban").text
    assert "#00ff99" in with_color

    logged_in_client.post(
        f"/kanban/swimlanes/{swimlane_id}/color", data={"color": "#00ff99", "clear_color": "true"}
    )
    without_color = logged_in_client.get("/kanban").text
    assert "#00ff99" not in without_color


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
