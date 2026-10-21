def test_pomodoro_state_idle_by_default(logged_in_client):
    response = logged_in_client.get("/pomodoro/state")
    assert response.status_code == 200
    data = response.json()
    assert data["active"] is None
    assert data["default_work_minutes"] == 25
    assert data["default_break_minutes"] == 5


def test_pomodoro_start_and_state(logged_in_client):
    start = logged_in_client.post("/pomodoro/start", data={"phase": "work", "minutes": "25"})
    assert start.status_code == 200
    session = start.json()
    assert session["phase"] == "work"
    assert session["status"] == "running"

    state = logged_in_client.get("/pomodoro/state").json()
    assert state["active"]["id"] == session["id"]

    finish = logged_in_client.post(f"/pomodoro/{session['id']}/finish")
    assert finish.status_code == 200

    state_after = logged_in_client.get("/pomodoro/state").json()
    assert state_after["active"] is None


def test_pomodoro_start_cancels_previous_running_session(logged_in_client):
    first = logged_in_client.post("/pomodoro/start", data={"phase": "work", "minutes": "25"}).json()
    second = logged_in_client.post("/pomodoro/start", data={"phase": "work", "minutes": "10"}).json()

    state = logged_in_client.get("/pomodoro/state").json()
    assert state["active"]["id"] == second["id"]
    assert first["id"] != second["id"]


def test_pomodoro_start_with_invalid_phase_rejected(logged_in_client):
    response = logged_in_client.post("/pomodoro/start", data={"phase": "nap", "minutes": "25"})
    assert response.status_code == 400


def test_pomodoro_tasks_lists_only_open_tasks(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Open taak", "description": "", "deadline": "", "tags": ""})
    response = logged_in_client.get("/pomodoro/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Open taak" in titles


def test_pomodoro_markup_has_new_design_controls(logged_in_client):
    page = logged_in_client.get("/tasks").text
    for element_id in ["pomodoro-reset-btn", "pomodoro-skip-btn", "pomodoro-ticks", "pomodoro-toggle-btn", "sidebar-pomodoro-btn"]:
        assert f'id="{element_id}"' in page
    assert 'class="pomodoro-time-min"' in page and 'class="pomodoro-time-sec"' in page


def test_pomodoro_menu_button_stays_in_dom_when_hidden_from_navigation(logged_in_client):
    """pomodoro.js stopt als #pomodoro-menu-btn ontbreekt; dan werkte ook de ▶-knop bij een taak
    niet meer. De knop blijft daarom altijd bestaan (alleen `hidden` als de module verborgen is)."""
    keys = ["tasks", "kanban", "mindmap", "notes", "stickies", "snippets", "calendar", "search", "graph"]
    logged_in_client.post("/settings/navigation", data={"visible": keys, "redirect_to": "/account"})
    page = logged_in_client.get("/tasks").text
    assert 'id="pomodoro-menu-btn" class="nav-item" hidden' in page

    logged_in_client.post("/settings/navigation", data={"visible": keys + ["pomodoro"], "redirect_to": "/account"})
    page = logged_in_client.get("/tasks").text
    assert 'id="pomodoro-menu-btn" class="nav-item" >' in page.replace("  ", " ") or 'id="pomodoro-menu-btn" class="nav-item" ' in page
    assert 'id="pomodoro-menu-btn" class="nav-item" hidden' not in page
    logged_in_client.post("/settings/navigation", data={"visible": keys + ["pomodoro"], "redirect_to": "/account"})
