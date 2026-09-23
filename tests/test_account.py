import re
from datetime import date, timedelta

from app.database import SessionLocal
from app.models.user import User
from app.services.stats import compute_user_stats


def test_default_password_banner_visible(logged_in_client):
    response = logged_in_client.get("/tasks")
    assert "standaard-wachtwoord" in response.text


def test_change_password_clears_banner_and_can_be_reverted(logged_in_client):
    response = logged_in_client.post(
        "/account",
        data={
            "current_password": "testpass",
            "new_username": "admin",
            "new_password": "nieuwgeheim",
            "new_password_confirm": "nieuwgeheim",
        },
    )
    assert response.status_code == 200
    assert "Opgeslagen" in response.text

    tasks_page = logged_in_client.get("/tasks")
    assert "standaard-wachtwoord" not in tasks_page.text

    # Zet het wachtwoord terug zodat andere tests (en fixtures) niet worden geraakt.
    revert = logged_in_client.post(
        "/account",
        data={
            "current_password": "nieuwgeheim",
            "new_username": "admin",
            "new_password": "testpass",
            "new_password_confirm": "testpass",
        },
    )
    assert revert.status_code == 200


def test_change_password_wrong_current_password(logged_in_client):
    response = logged_in_client.post(
        "/account",
        data={
            "current_password": "verkeerd",
            "new_username": "admin",
            "new_password": "",
            "new_password_confirm": "",
        },
    )
    assert response.status_code == 401


def test_account_page_shows_statistics_section(logged_in_client):
    response = logged_in_client.get("/account")
    assert response.status_code == 200
    assert "Statistieken" in response.text
    assert "Pomodoro's opgestart" in response.text
    assert "Deadlines gehaald" in response.text


def test_stats_reflect_task_completion_and_priority(logged_in_client):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "admin").first()
        before = compute_user_stats(db, user.id)

    logged_in_client.post(
        "/tasks", data={"title": "Stats hoge prio", "description": "", "deadline": "", "tags": "", "priority": "true"}
    )
    listing = logged_in_client.get("/tasks").text
    idx = listing.rindex("Stats hoge prio")
    task_id = re.findall(r'href="/tasks/(\d+)/edit"', listing[:idx])[-1]

    with SessionLocal() as db:
        after_create = compute_user_stats(db, user.id)
    assert after_create["tasks"]["high_priority_open"] == before["tasks"]["high_priority_open"] + 1
    assert after_create["tasks"]["total"] == before["tasks"]["total"] + 1

    logged_in_client.post(f"/tasks/{task_id}/toggle-done")
    with SessionLocal() as db:
        after_done = compute_user_stats(db, user.id)
    assert after_done["tasks"]["high_priority_open"] == before["tasks"]["high_priority_open"]
    assert after_done["tasks"]["done"] == before["tasks"]["done"] + 1
    assert after_done["tasks"]["deadlines_met"] == before["tasks"]["deadlines_met"]

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")


def test_openai_key_save_show_masked_and_clear(logged_in_client):
    account_page = logged_in_client.get("/account").text
    assert "Nog geen sleutel ingesteld" in account_page

    logged_in_client.post("/account/openai-key", data={"openai_api_key": "sk-testsleutel1234"})
    after_save = logged_in_client.get("/account").text
    assert "eindigt op ...1234" in after_save
    assert "sk-testsleutel1234" not in after_save

    logged_in_client.post("/account/openai-key/clear")
    after_clear = logged_in_client.get("/account").text
    assert "Nog geen sleutel ingesteld" in after_clear


def test_stats_deadline_met_when_completed_on_time(logged_in_client):
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == "admin").first()
        before = compute_user_stats(db, user.id)

    logged_in_client.post(
        "/tasks",
        data={
            "title": "Deadline gehaald",
            "description": "",
            "deadline": (date.today() + timedelta(days=1)).isoformat(),
            "tags": "",
        },
    )
    listing = logged_in_client.get("/tasks").text
    idx = listing.rindex("Deadline gehaald")
    task_id = re.findall(r'href="/tasks/(\d+)/edit"', listing[:idx])[-1]
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")

    with SessionLocal() as db:
        after = compute_user_stats(db, user.id)
    assert after["tasks"]["deadlines_met"] == before["tasks"]["deadlines_met"] + 1

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")
