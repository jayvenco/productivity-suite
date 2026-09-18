import re


def _create_board(logged_in_client, name: str = "Testmindmap") -> int:
    response = logged_in_client.post("/mindmap", data={"name": name}, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["location"]
    return int(location.rsplit("/", 1)[-1])


def test_mindmap_list_requires_login(client):
    response = client.get("/mindmap", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_empty_mindmap_list(logged_in_client):
    page = logged_in_client.get("/mindmap").text
    assert "Nog geen mindmaps" in page


def test_create_mindmap_seeds_a_default_node(logged_in_client):
    board_id = _create_board(logged_in_client, "Mijn eerste mindmap")

    page = logged_in_client.get(f"/mindmap/{board_id}").text
    assert "Hoofdonderwerp" in page
    assert 'class="mindmap-node"' in page

    listing = logged_in_client.get("/mindmap").text
    assert "Mijn eerste mindmap" in listing


def test_create_multiple_mindmaps_are_listed_separately(logged_in_client):
    _create_board(logged_in_client, "Werk-mindmap")
    _create_board(logged_in_client, "Privé-mindmap")

    listing = logged_in_client.get("/mindmap").text
    assert "Werk-mindmap" in listing
    assert "Privé-mindmap" in listing


def test_rename_mindmap(logged_in_client):
    board_id = _create_board(logged_in_client, "Oude naam")

    response = logged_in_client.post(f"/mindmap/{board_id}/rename", data={"name": "Nieuwe naam"})
    assert response.status_code == 200
    assert response.json()["name"] == "Nieuwe naam"

    listing = logged_in_client.get("/mindmap").text
    assert "Nieuwe naam" in listing
    assert "Oude naam" not in listing


def test_delete_mindmap_removes_it_from_list(logged_in_client):
    board_id = _create_board(logged_in_client, "Weg ermee")

    response = logged_in_client.post(f"/mindmap/{board_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/mindmap"

    listing = logged_in_client.get("/mindmap").text
    assert "Weg ermee" not in listing


def test_create_node(logged_in_client):
    board_id = _create_board(logged_in_client)

    response = logged_in_client.post(
        f"/mindmap/{board_id}/nodes", data={"text": "Zijtak", "color": "#50fa7b", "x": "200", "y": "150"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Zijtak"
    assert body["color"] == "#50fa7b"
    assert body["x"] == 200
    assert body["y"] == 150
    assert body["edge"] is None

    page = logged_in_client.get(f"/mindmap/{board_id}").text
    assert "Zijtak" in page


def test_create_node_with_parent_also_creates_edge(logged_in_client):
    board_id = _create_board(logged_in_client)
    page = logged_in_client.get(f"/mindmap/{board_id}").text
    parent_id = re.search(r'data-node-id="(\d+)"', page).group(1)

    response = logged_in_client.post(
        f"/mindmap/{board_id}/nodes",
        data={"text": "Kind-idee", "color": "#ff5555", "x": "300", "y": "300", "parent_id": parent_id},
    )
    body = response.json()
    assert body["edge"] is not None
    assert body["edge"]["from_node_id"] == int(parent_id)
    assert body["edge"]["to_node_id"] == body["id"]


def test_update_node_text_and_color(logged_in_client):
    board_id = _create_board(logged_in_client)
    create = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Origineel", "color": "#bd93f9"})
    node_id = create.json()["id"]

    response = logged_in_client.post(
        f"/mindmap/nodes/{node_id}", data={"text": "Bijgewerkt", "color": "#8be9fd"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Bijgewerkt"
    assert body["color"] == "#8be9fd"


def test_update_node_position(logged_in_client):
    board_id = _create_board(logged_in_client)
    create = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Verplaatsbaar"})
    node_id = create.json()["id"]

    response = logged_in_client.post(f"/mindmap/nodes/{node_id}", data={"x": "500", "y": "400"})
    body = response.json()
    assert body["x"] == 500
    assert body["y"] == 400


def test_delete_node_removes_it_and_its_edges(logged_in_client):
    board_id = _create_board(logged_in_client)
    a = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "A"}).json()
    b = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "B"}).json()
    edge = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}
    ).json()

    response = logged_in_client.post(f"/mindmap/nodes/{a['id']}/delete")
    assert response.status_code == 200

    page = logged_in_client.get(f"/mindmap/{board_id}").text
    assert f'data-node-id="{a["id"]}"' not in page
    assert f'"id": {edge["id"]}' not in page


def test_create_edge_between_existing_nodes(logged_in_client):
    board_id = _create_board(logged_in_client)
    a = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Knoop A"}).json()
    b = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Knoop B"}).json()

    response = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_node_id"] == a["id"]
    assert body["to_node_id"] == b["id"]

    page = logged_in_client.get(f"/mindmap/{board_id}").text
    assert f'"from_node_id": {a["id"]}, "to_node_id": {b["id"]}' in page


def test_create_edge_rejects_self_link(logged_in_client):
    board_id = _create_board(logged_in_client)
    a = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Alleen"}).json()

    response = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": a["id"]}
    )
    assert response.status_code == 400


def test_create_edge_rejects_nodes_from_different_boards(logged_in_client):
    board_a = _create_board(logged_in_client, "Bord A")
    board_b = _create_board(logged_in_client, "Bord B")
    a = logged_in_client.post(f"/mindmap/{board_a}/nodes", data={"text": "In A"}).json()
    b = logged_in_client.post(f"/mindmap/{board_b}/nodes", data={"text": "In B"}).json()

    response = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}
    )
    assert response.status_code == 400


def test_create_duplicate_edge_returns_existing(logged_in_client):
    board_id = _create_board(logged_in_client)
    a = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Duplo A"}).json()
    b = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "Duplo B"}).json()

    first = logged_in_client.post("/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}).json()
    second = logged_in_client.post("/mindmap/edges", data={"from_node_id": b["id"], "to_node_id": a["id"]}).json()

    assert first["id"] == second["id"]


def test_delete_edge(logged_in_client):
    board_id = _create_board(logged_in_client)
    a = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "E1"}).json()
    b = logged_in_client.post(f"/mindmap/{board_id}/nodes", data={"text": "E2"}).json()
    edge = logged_in_client.post("/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}).json()

    response = logged_in_client.post(f"/mindmap/edges/{edge['id']}/delete")
    assert response.status_code == 200

    page = logged_in_client.get(f"/mindmap/{board_id}").text
    assert f'"id": {edge["id"]}' not in page


def test_cannot_edit_nonexistent_node(logged_in_client):
    response = logged_in_client.post("/mindmap/nodes/999999", data={"text": "x"})
    assert response.status_code == 404


def test_cannot_view_nonexistent_mindmap(logged_in_client):
    response = logged_in_client.get("/mindmap/999999")
    assert response.status_code == 404
