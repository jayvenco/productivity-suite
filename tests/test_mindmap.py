import re


def test_mindmap_requires_login(client):
    response = client.get("/mindmap", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_visiting_mindmap_seeds_a_default_node(logged_in_client):
    page = logged_in_client.get("/mindmap").text
    assert "Hoofdonderwerp" in page
    assert 'class="mindmap-node"' in page


def test_create_node(logged_in_client):
    response = logged_in_client.post(
        "/mindmap/nodes", data={"text": "Zijtak", "color": "#50fa7b", "x": "200", "y": "150"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Zijtak"
    assert body["color"] == "#50fa7b"
    assert body["x"] == 200
    assert body["y"] == 150
    assert body["edge"] is None

    page = logged_in_client.get("/mindmap").text
    assert "Zijtak" in page


def test_create_node_with_parent_also_creates_edge(logged_in_client):
    logged_in_client.get("/mindmap")  # zorgt dat het bord (met Hoofdonderwerp) bestaat
    page = logged_in_client.get("/mindmap").text
    parent_id = re.search(r'data-node-id="(\d+)"', page).group(1)

    response = logged_in_client.post(
        "/mindmap/nodes",
        data={"text": "Kind-idee", "color": "#ff5555", "x": "300", "y": "300", "parent_id": parent_id},
    )
    body = response.json()
    assert body["edge"] is not None
    assert body["edge"]["from_node_id"] == int(parent_id)
    assert body["edge"]["to_node_id"] == body["id"]


def test_update_node_text_and_color(logged_in_client):
    create = logged_in_client.post("/mindmap/nodes", data={"text": "Origineel", "color": "#bd93f9"})
    node_id = create.json()["id"]

    response = logged_in_client.post(
        f"/mindmap/nodes/{node_id}", data={"text": "Bijgewerkt", "color": "#8be9fd"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "Bijgewerkt"
    assert body["color"] == "#8be9fd"


def test_update_node_position(logged_in_client):
    create = logged_in_client.post("/mindmap/nodes", data={"text": "Verplaatsbaar"})
    node_id = create.json()["id"]

    response = logged_in_client.post(f"/mindmap/nodes/{node_id}", data={"x": "500", "y": "400"})
    body = response.json()
    assert body["x"] == 500
    assert body["y"] == 400


def test_delete_node_removes_it_and_its_edges(logged_in_client):
    a = logged_in_client.post("/mindmap/nodes", data={"text": "A"}).json()
    b = logged_in_client.post("/mindmap/nodes", data={"text": "B"}).json()
    edge = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}
    ).json()

    response = logged_in_client.post(f"/mindmap/nodes/{a['id']}/delete")
    assert response.status_code == 200

    page = logged_in_client.get("/mindmap").text
    assert f'data-node-id="{a["id"]}"' not in page
    assert f'"id": {edge["id"]}' not in page


def test_create_edge_between_existing_nodes(logged_in_client):
    a = logged_in_client.post("/mindmap/nodes", data={"text": "Knoop A"}).json()
    b = logged_in_client.post("/mindmap/nodes", data={"text": "Knoop B"}).json()

    response = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_node_id"] == a["id"]
    assert body["to_node_id"] == b["id"]

    page = logged_in_client.get("/mindmap").text
    assert f'"from_node_id": {a["id"]}, "to_node_id": {b["id"]}' in page


def test_create_edge_rejects_self_link(logged_in_client):
    a = logged_in_client.post("/mindmap/nodes", data={"text": "Alleen"}).json()

    response = logged_in_client.post(
        "/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": a["id"]}
    )
    assert response.status_code == 400


def test_create_duplicate_edge_returns_existing(logged_in_client):
    a = logged_in_client.post("/mindmap/nodes", data={"text": "Duplo A"}).json()
    b = logged_in_client.post("/mindmap/nodes", data={"text": "Duplo B"}).json()

    first = logged_in_client.post("/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}).json()
    second = logged_in_client.post("/mindmap/edges", data={"from_node_id": b["id"], "to_node_id": a["id"]}).json()

    assert first["id"] == second["id"]


def test_delete_edge(logged_in_client):
    a = logged_in_client.post("/mindmap/nodes", data={"text": "E1"}).json()
    b = logged_in_client.post("/mindmap/nodes", data={"text": "E2"}).json()
    edge = logged_in_client.post("/mindmap/edges", data={"from_node_id": a["id"], "to_node_id": b["id"]}).json()

    response = logged_in_client.post(f"/mindmap/edges/{edge['id']}/delete")
    assert response.status_code == 200

    page = logged_in_client.get("/mindmap").text
    assert f'"id": {edge["id"]}' not in page


def test_cannot_edit_other_boards_node(logged_in_client):
    response = logged_in_client.post("/mindmap/nodes/999999", data={"text": "x"})
    assert response.status_code == 404
