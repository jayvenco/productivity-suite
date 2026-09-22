import re
from datetime import date, timedelta

from app.services.calendar_grid import add_months, month_weeks, week_dates


def _event_id_for_title(html: str, title: str) -> str:
    """Zoekt het event-id horend bij deze titel (de pagina kan events uit
    eerdere tests bevatten). Zoekt terug vanaf de titel naar de
    dichtstbijzijnde voorgaande /calendar/events/<id>/edit-link."""
    marker = f'title="{title}">{title}</a>'
    idx = html.index(marker)
    matches = list(re.finditer(r'/calendar/events/(\d+)/edit', html[:idx]))
    assert matches, f"Event met titel {title!r} niet gevonden"
    return matches[-1].group(1)


def test_calendar_requires_login(client):
    response = client.get("/calendar", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_month_view_shows_title_and_grid(logged_in_client):
    response = logged_in_client.get("/calendar?year=2026&month=3")
    assert response.status_code == 200
    assert "maart 2026" in response.text
    assert "calendar-grid-month" in response.text


def test_week_view_shows_title_and_grid(logged_in_client):
    response = logged_in_client.get("/calendar?view=week&day=2026-03-10")
    assert response.status_code == 200
    assert "Week van" in response.text
    assert "calendar-grid-week" in response.text


def test_create_and_show_event_on_calendar(logged_in_client):
    create = logged_in_client.post(
        "/calendar/events",
        data={"title": "Tandarts", "event_date": "2026-03-15", "description": "", "tags": "afspraak"},
        follow_redirects=False,
    )
    assert create.status_code == 303

    page = logged_in_client.get("/calendar?year=2026&month=3").text
    assert "Tandarts" in page
    assert "calendar-item-event" in page


def test_task_deadline_shows_up_on_calendar(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Deadline-taak", "description": "", "deadline": "2026-03-20", "tags": ""}
    )
    page = logged_in_client.get("/calendar?year=2026&month=3").text
    assert "Deadline-taak" in page
    assert "calendar-item-task" in page


def test_edit_event(logged_in_client):
    logged_in_client.post(
        "/calendar/events", data={"title": "Origineel", "event_date": "2026-03-05", "description": "", "tags": ""}
    )
    page = logged_in_client.get("/calendar?year=2026&month=3").text
    event_id = _event_id_for_title(page, "Origineel")

    update = logged_in_client.post(
        f"/calendar/events/{event_id}",
        data={"title": "Bijgewerkt", "event_date": "2026-03-06", "description": "", "tags": ""},
        follow_redirects=False,
    )
    assert update.status_code == 303

    page_after = logged_in_client.get("/calendar?year=2026&month=3").text
    assert "Bijgewerkt" in page_after
    assert "Origineel" not in page_after


def test_delete_event(logged_in_client):
    logged_in_client.post(
        "/calendar/events", data={"title": "Te verwijderen", "event_date": "2026-03-08", "description": "", "tags": ""}
    )
    page = logged_in_client.get("/calendar?year=2026&month=3").text
    event_id = _event_id_for_title(page, "Te verwijderen")

    response = logged_in_client.post(f"/calendar/events/{event_id}/delete", follow_redirects=False)
    assert response.status_code == 303

    page_after = logged_in_client.get("/calendar?year=2026&month=3").text
    assert "Te verwijderen" not in page_after


def test_cannot_edit_other_users_event_scope(logged_in_client):
    """Een niet-bestaand event-id geeft 404 (dekt ook de eigenaarschap-check)."""
    response = logged_in_client.get("/calendar/events/999999/edit")
    assert response.status_code == 404


def test_month_weeks_covers_full_weeks():
    weeks = month_weeks(2026, 3)
    assert all(len(week) == 7 for week in weeks)
    assert weeks[0][0].weekday() == 0  # maandag
    all_days = [d for week in weeks for d in week]
    assert date(2026, 3, 1) in all_days
    assert date(2026, 3, 31) in all_days


def test_week_dates_returns_monday_to_sunday():
    days = week_dates(date(2026, 3, 12))  # een donderdag
    assert len(days) == 7
    assert days[0].weekday() == 0
    assert days[-1].weekday() == 6
    assert days[-1] - days[0] == timedelta(days=6)


def test_add_months_handles_year_rollover():
    assert add_months(2026, 12, 1) == (2027, 1)
    assert add_months(2026, 1, -1) == (2025, 12)


def test_widget_requires_login(client):
    response = client.get("/calendar/widget", follow_redirects=False)
    assert response.status_code == 303


def test_widget_returns_month_grid_with_label(logged_in_client):
    response = logged_in_client.get("/calendar/widget?year=2026&month=3")
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "maart 2026"
    assert len(data["day_labels"]) == 7
    assert all(len(week) == 7 for week in data["weeks"])
    assert data["prev"] == {"year": 2026, "month": 2}
    assert data["next"] == {"year": 2026, "month": 4}


def test_widget_marks_days_with_task_deadline(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Widget-taak", "description": "", "deadline": "2026-03-12", "tags": ""}
    )
    data = logged_in_client.get("/calendar/widget?year=2026&month=3").json()
    day = next(d for week in data["weeks"] for d in week if d["date"] == "2026-03-12")
    assert day["has_items"] is True

    other_day = next(d for week in data["weeks"] for d in week if d["date"] == "2026-03-13")
    assert other_day["has_items"] is False


def test_widget_marks_days_with_calendar_event(logged_in_client):
    logged_in_client.post(
        "/calendar/events", data={"title": "Widget-event", "event_date": "2026-03-19", "description": "", "tags": ""}
    )
    data = logged_in_client.get("/calendar/widget?year=2026&month=3").json()
    day = next(d for week in data["weeks"] for d in week if d["date"] == "2026-03-19")
    assert day["has_items"] is True


def test_quick_create_task_appears_in_task_list(logged_in_client):
    response = logged_in_client.post("/tasks/quick", data={"title": "Snel toegevoegd", "deadline": "2026-04-01"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Snel toegevoegd"
    assert body["deadline"] == "2026-04-01"

    listing = logged_in_client.get("/tasks").text
    assert "Snel toegevoegd" in listing


def test_quick_create_task_without_deadline(logged_in_client):
    response = logged_in_client.post("/tasks/quick", data={"title": "Zonder deadline"})
    assert response.status_code == 200
    assert response.json()["deadline"] is None


def test_quick_create_task_requires_title(logged_in_client):
    response = logged_in_client.post("/tasks/quick", data={"title": "   "})
    assert response.status_code == 400


def test_home_redirects_to_calendar(logged_in_client):
    response = logged_in_client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/calendar"


def test_calendar_overview_shows_high_priority_task(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Hoge prio taak", "description": "", "deadline": "", "tags": "", "priority": "true"}
    )
    page = logged_in_client.get("/calendar").text
    assert "Hoge prio taak" in page


def test_calendar_overview_hides_low_priority_task(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Lage prio taak", "description": "", "deadline": "", "tags": ""})
    page = logged_in_client.get("/calendar").text
    assert "Lage prio taak" not in page


def test_calendar_overview_hides_done_high_priority_task(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Klaar hoge prio", "description": "", "deadline": "", "tags": "", "priority": "true"}
    )
    listing = logged_in_client.get("/tasks").text
    idx = listing.index("Klaar hoge prio")
    task_id = re.findall(r'href="/tasks/(\d+)/edit"', listing[:idx])[-1]
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")

    page = logged_in_client.get("/calendar").text
    assert "Klaar hoge prio" not in page

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")


def test_calendar_overview_shows_recent_notes(logged_in_client):
    logged_in_client.post("/notes", data={"title": "Kalendernotitie", "content": "", "tags": ""})
    page = logged_in_client.get("/calendar").text
    assert "Kalendernotitie" in page


def test_calendar_overview_shows_recent_kanban_card(logged_in_client):
    board_html = logged_in_client.get("/kanban").text
    column_id = re.search(r'data-column-id="(\d+)"', board_html).group(1)
    swimlane_id = re.search(r'data-swimlane-id="(\d+)"', board_html).group(1)
    logged_in_client.post(
        "/kanban/cards",
        data={"column_id": column_id, "swimlane_id": swimlane_id, "title": "Kalenderkaart", "description": ""},
    )
    page = logged_in_client.get("/calendar").text
    assert "Kalenderkaart" in page


def test_quickadd_wheel_links_to_every_creation_page(logged_in_client):
    page = logged_in_client.get("/calendar").text
    for href in ["/notes/new", "/kanban", "/snippets/new", "/tasks/new", "/mindmap"]:
        assert f'href="{href}" class="quickadd-spoke"' in page
