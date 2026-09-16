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
