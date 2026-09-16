from datetime import date, timedelta


def test_create_and_list_task(logged_in_client):
    response = logged_in_client.post(
        "/tasks",
        data={"title": "Test taak", "description": "Iets doen", "deadline": "", "tags": "werk, later"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    listing = logged_in_client.get("/tasks")
    assert listing.status_code == 200
    assert "Test taak" in listing.text
    assert "werk" in listing.text


def test_task_requires_login(client):
    response = client.get("/tasks", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_priority_task_shown_and_sorted_first(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Normale taak", "description": "", "deadline": "", "tags": ""})
    logged_in_client.post(
        "/tasks",
        data={"title": "Belangrijke taak", "description": "", "deadline": "", "tags": "", "priority": "true"},
    )

    listing = logged_in_client.get("/tasks").text
    assert "priority-star" in listing
    assert listing.index("Belangrijke taak") < listing.index("Normale taak")


def test_deadline_bar_color_present_for_near_deadline(logged_in_client):
    near_deadline = (date.today() + timedelta(days=2)).isoformat()
    logged_in_client.post(
        "/tasks",
        data={"title": "Bijna deadline", "description": "", "deadline": near_deadline, "tags": ""},
    )
    listing = logged_in_client.get("/tasks").text
    assert "deadline-bar" in listing
    assert "hsl(" in listing
