import re


def _first_ids(html: str):
    column_id = re.search(r'data-column-id="(\d+)"', html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', html).group(1)
    return column_id, swimlane_id


def test_search_requires_login(client):
    response = client.get("/search", params={"q": "iets"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_search_without_query_shows_prompt(logged_in_client):
    response = logged_in_client.get("/search")
    assert response.status_code == 200
    assert "Typ een woord of kies een tag" in response.text


def test_search_by_word_finds_task_and_note(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Boodschappen doen", "description": "melk en brood", "deadline": "", "tags": ""}
    )
    logged_in_client.post("/notes", data={"title": "Vergeet niets", "content": "boodschappenlijst", "tags": ""})
    logged_in_client.post("/notes", data={"title": "Onrelevant", "content": "iets anders", "tags": ""})

    response = logged_in_client.get("/search", params={"q": "boodschap"})
    assert response.status_code == 200
    assert "Boodschappen doen" in response.text
    assert "Vergeet niets" in response.text
    assert "Onrelevant" not in response.text


def test_search_by_tag_finds_items_across_types(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Getagde taak", "description": "", "deadline": "", "tags": "zoektag"}
    )
    logged_in_client.post("/notes", data={"title": "Getagde notitie", "content": "", "tags": "zoektag"})
    logged_in_client.post("/mindmap", data={"name": "Getagde mindmap", "tags": "zoektag"})
    logged_in_client.post("/notes", data={"title": "Andere notitie", "content": "", "tags": "andere-tag"})

    response = logged_in_client.get("/search", params={"tag": "zoektag"})
    assert response.status_code == 200
    assert "Getagde taak" in response.text
    assert "Getagde notitie" in response.text
    assert "Getagde mindmap" in response.text
    assert "Andere notitie" not in response.text


def test_search_finds_kanban_card_and_snippet_and_event(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id, swimlane_id = _first_ids(board_html)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Uniekekaartnaam", "description": "", "tags": ""},
    )
    logged_in_client.post("/snippets", data={"title": "Uniekesnippetnaam", "tags": ""})
    logged_in_client.post(
        "/calendar/events",
        data={"title": "Uniekeafspraaknaam", "event_date": "2026-01-15", "description": "", "tags": ""},
    )

    response = logged_in_client.get("/search", params={"q": "uniekek"})
    assert "Uniekekaartnaam" in response.text

    response = logged_in_client.get("/search", params={"q": "uniekes"})
    assert "Uniekesnippetnaam" in response.text

    response = logged_in_client.get("/search", params={"q": "uniekea"})
    assert "Uniekeafspraaknaam" in response.text


def test_search_combines_word_and_tag_filters(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Combi match", "description": "", "deadline": "", "tags": "combitag"}
    )
    logged_in_client.post(
        "/tasks", data={"title": "Combi geen tag", "description": "", "deadline": "", "tags": ""}
    )
    logged_in_client.post(
        "/tasks", data={"title": "Andere titel", "description": "", "deadline": "", "tags": "combitag"}
    )

    response = logged_in_client.get("/search", params={"q": "combi match", "tag": "combitag"})
    assert "Combi match" in response.text
    assert "Combi geen tag" not in response.text
    assert "Andere titel" not in response.text
