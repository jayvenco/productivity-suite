import re

from app.services.kanban_progress import swimlane_progress


def test_progress_formula():
    assert swimlane_progress([0, 0, 0, 0, 0]) == {"percent": 0, "cards": 0, "filled": 0}
    assert swimlane_progress([4, 0, 0, 0, 0])["percent"] == 0  # alles nog in de eerste kolom
    assert swimlane_progress([0, 0, 0, 0, 4])["percent"] == 100
    assert swimlane_progress([1, 1, 1, 1, 1])["percent"] == 50  # 0/25/50/75/100 gemiddeld
    two = swimlane_progress([1, 1, 0, 0, 2])  # (0 + 25 + 100*2) / 4 = 56
    assert two["percent"] == 56 and two["filled"] == 6 and two["cards"] == 4
    assert swimlane_progress([3])["percent"] == 0  # één kolom: geen voortgang te meten


def test_board_shows_ten_dots_per_swimlane_before_edit_button(logged_in_client):
    page = logged_in_client.get("/kanban").text
    widget = re.search(r'<div class="swimlane-progress".*?</div>', page, re.S).group(0)
    assert widget.count("swimlane-progress-dot") == 10 and "swimlane-progress-label" in widget
    assert page.index('class="swimlane-progress"') < page.index('class="swimlane-rename-form"')


def test_progress_updates_when_a_card_moves(logged_in_client):
    """Eigen swimlane, zodat kaarten uit andere tests de uitkomst niet beïnvloeden."""
    logged_in_client.post("/kanban/swimlanes", data={"name": "Voortgangs-lane"})
    board = logged_in_client.get("/kanban").text
    block = board[board.index("Voortgangs-lane"):]
    swimlane = re.search(r'data-swimlane-id="(\d+)"', block).group(1)
    lane_cols = re.findall(rf'data-column-id="(\d+)" data-swimlane-id="{swimlane}"', board)
    assert len(lane_cols) == 5

    def widget():
        page = logged_in_client.get("/kanban").text
        return re.search(rf'data-swimlane-progress="{swimlane}".*?</div>', page, re.S).group(0)

    assert "0%" in widget() and "swimlane-progress-dot filled" not in widget()  # lege lane

    logged_in_client.post("/kanban/cards", data={"column_id": lane_cols[0], "swimlane_id": swimlane, "title": "Voortgangskaart"})
    page = logged_in_client.get("/kanban").text
    card_id = re.search(r'data-card-id="(\d+)"[^>]*>\s*<div class="card-title">Voortgangskaart', page).group(1)
    assert "0%" in widget()  # nog in Backlog

    logged_in_client.post(f"/kanban/cards/{card_id}/move", data={"column_id": lane_cols[-1], "swimlane_id": swimlane, "position": "0"})
    done = widget()
    assert done.count("swimlane-progress-dot filled") == 10 and "100%" in done

    logged_in_client.post(f"/kanban/swimlanes/{swimlane}/delete")
