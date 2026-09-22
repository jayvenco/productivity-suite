import re

from app.database import SessionLocal
from app.models.user import User
from app.services.stats import compute_activity_charts


def test_stats_page_requires_login(client):
    response = client.get("/stats", follow_redirects=False)
    assert response.status_code in (302, 303, 401)


def test_stats_page_loads_with_charts(logged_in_client):
    response = logged_in_client.get("/stats")
    assert response.status_code == 200
    assert "Focustijd per dag" in response.text
    assert "Focustijd per maand" in response.text
    assert "Aangemaakt vs. afgerond" in response.text


def test_created_task_increments_todays_created_bar(logged_in_client):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "admin").first()
        before = compute_activity_charts(db, user.id)
    before_today = before["items_by_day"][-1]["created"]

    logged_in_client.post(
        "/tasks", data={"title": "Statistiek-test taak", "description": "", "deadline": "", "tags": ""}
    )
    listing = logged_in_client.get("/tasks").text
    idx = listing.rindex("Statistiek-test taak")
    task_id = re.findall(r'href="/tasks/(\d+)/edit"', listing[:idx])[-1]

    with SessionLocal() as db:
        after = compute_activity_charts(db, user.id)
    assert after["items_by_day"][-1]["created"] == before_today + 1

    logged_in_client.post(f"/tasks/{task_id}/delete")


def test_done_task_increments_todays_done_bar(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Statistiek-test afgerond", "description": "", "deadline": "", "tags": ""}
    )
    listing = logged_in_client.get("/tasks").text
    idx = listing.rindex("Statistiek-test afgerond")
    task_id = re.findall(r'href="/tasks/(\d+)/edit"', listing[:idx])[-1]

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "admin").first()
        before = compute_activity_charts(db, user.id)
    before_today = before["items_by_day"][-1]["done"]

    logged_in_client.post(f"/tasks/{task_id}/toggle-done")
    with SessionLocal() as db:
        after = compute_activity_charts(db, user.id)
    assert after["items_by_day"][-1]["done"] == before_today + 1

    logged_in_client.post(f"/tasks/{task_id}/delete")
