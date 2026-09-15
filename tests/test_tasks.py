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
