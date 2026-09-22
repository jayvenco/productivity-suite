import re


def test_graph_requires_login(client):
    response = client.get("/graph", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_graph_page_loads(logged_in_client):
    response = logged_in_client.get("/graph")
    assert response.status_code == 200
    assert "Graph" in response.text


def test_graph_data_returns_json_shape(logged_in_client):
    response = logged_in_client.get("/graph/data")
    assert response.status_code == 200
    body = response.json()
    assert "nodes" in body
    assert "edges" in body
    assert isinstance(body["nodes"], list)
    assert isinstance(body["edges"], list)


def test_graph_data_includes_tagged_task(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Graaf-taak-uniek", "description": "", "deadline": "", "tags": "gedeeld-uniek"}
    )
    body = logged_in_client.get("/graph/data").json()
    labels = {n["label"] for n in body["nodes"]}
    assert "Graaf-taak-uniek" in labels
    assert "#gedeeld-uniek" in labels

    task_node = next(n for n in body["nodes"] if n["label"] == "Graaf-taak-uniek")
    tag_node = next(n for n in body["nodes"] if n["label"] == "#gedeeld-uniek")
    assert task_node["type"] == "task"
    assert tag_node["type"] == "tag"
    assert {"source": task_node["id"], "target": tag_node["id"]} in body["edges"]


def test_graph_data_excludes_untagged_items(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Geen tag", "description": "", "deadline": "", "tags": ""})
    body = logged_in_client.get("/graph/data").json()
    labels = {n["label"] for n in body["nodes"]}
    assert "Geen tag" not in labels


def test_graph_data_links_different_item_types_via_shared_tag(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Gedeelde taak", "description": "", "deadline": "", "tags": "samen-uniek"}
    )
    logged_in_client.post("/notes", data={"title": "Gedeelde notitie", "content": "", "tags": "samen-uniek"})

    board_html = logged_in_client.get("/kanban").text
    column_id = re.search(r'data-column-id="(\d+)"', board_html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', board_html).group(1)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Gedeelde kaart", "tags": "samen-uniek"},
    )
    mindmap_response = logged_in_client.post(
        "/mindmap", data={"name": "Gedeelde mindmap", "tags": "samen-uniek"}, follow_redirects=False
    )
    mindmap_id = int(mindmap_response.headers["location"].rsplit("/", 1)[-1])

    body = logged_in_client.get("/graph/data").json()
    tag_nodes = [n for n in body["nodes"] if n["type"] == "tag" and n["label"] == "#samen-uniek"]
    assert len(tag_nodes) == 1
    tag_id = tag_nodes[0]["id"]

    # Alle vier item-types moeten een edge hebben naar precies deze tag-node.
    linked_source_ids = {e["source"] for e in body["edges"] if e["target"] == tag_id}
    linked_types = {n["type"] for n in body["nodes"] if n["id"] in linked_source_ids}
    assert linked_types == {"task", "note", "kanban", "mindmap"}
    assert len(linked_source_ids) == 4

    # Opruimen zodat "lege lijst"-tests in andere modules (bv. test_mindmap.py)
    # niet stuklopen op deze hier aangemaakte mindmap.
    logged_in_client.post(f"/mindmap/{mindmap_id}/delete")


def test_graph_data_requires_login(client):
    response = client.get("/graph/data", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
