import re
from datetime import date, timedelta

from app.services.recurrence import next_occurrence, occurrences


def test_weekly_occurrences_in_range():
    result = occurrences(date(2026, 3, 2), "weekly", None, date(2026, 3, 9), date(2026, 3, 31))
    assert result == [date(2026, 3, 9), date(2026, 3, 16), date(2026, 3, 23), date(2026, 3, 30)]


def test_weekly_respects_until_and_start():
    assert occurrences(date(2026, 3, 2), "weekly", date(2026, 3, 16), date(2026, 3, 1), date(2026, 3, 31)) == [
        date(2026, 3, 2), date(2026, 3, 9), date(2026, 3, 16),
    ]
    assert occurrences(date(2026, 3, 20), "weekly", None, date(2026, 3, 1), date(2026, 3, 19)) == []


def test_monthly_clamps_to_month_end():
    result = occurrences(date(2026, 1, 31), "monthly", None, date(2026, 1, 1), date(2026, 4, 30))
    assert result == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]


def test_non_recurring_and_next_occurrence():
    assert occurrences(date(2026, 3, 2), "none", None, date(2026, 3, 1), date(2026, 3, 31)) == [date(2026, 3, 2)]
    assert next_occurrence(date(2020, 1, 1), "weekly", date(2020, 2, 1), date(2026, 1, 1)) is None
    assert next_occurrence(date(2020, 1, 15), "monthly", None, date(2026, 1, 1)) == date(2026, 1, 15)


def _create(client, title, start, recurrence, until=""):
    client.post(
        "/calendar/events",
        data={"title": title, "event_date": start.isoformat(), "description": "", "tags": "",
              "recurrence": recurrence, "recurrence_until": until},
    )


def _event_id(client, title):
    html = client.get("/calendar").text
    return re.search(rf'/calendar/events/(\d+)/edit"[^>]*>(?:↻ )?{re.escape(title)}<', html).group(1)


def test_weekly_event_shows_every_week_and_in_overview(logged_in_client):
    start = date.today().replace(day=1)
    _create(logged_in_client, "Wekelijkse sync", start, "weekly")

    page = logged_in_client.get(f"/calendar?year={start.year}&month={start.month}").text
    assert page.count("↻ Wekelijkse sync") >= 4
    overview = page[page.index("calendar-overview"):]
    assert "Herhalende afspraken" in overview and "wekelijks" in overview

    logged_in_client.post(f"/calendar/events/{_event_id(logged_in_client, 'Wekelijkse sync')}/delete")


def test_stop_recurrence_keeps_past_removes_future(logged_in_client):
    start = date.today() - timedelta(days=20)
    _create(logged_in_client, "Te stoppen reeks", start, "weekly")
    event_id = _event_id(logged_in_client, "Te stoppen reeks")

    response = logged_in_client.post(f"/calendar/events/{event_id}/stop-recurrence", follow_redirects=False)
    assert response.status_code == 303

    edit = logged_in_client.get(f"/calendar/events/{event_id}/edit").text
    assert f'value="{(start + timedelta(days=14)).isoformat()}"' in edit  # recurrence_until = laatste voorkomen
    overview = logged_in_client.get("/calendar").text
    assert "Te stoppen reeks" not in overview[overview.index("Herhalende afspraken"):overview.index("Hoge prioriteit")]

    logged_in_client.post(f"/calendar/events/{event_id}/delete")


def test_recurrence_until_field_is_saved(logged_in_client):
    start = date.today()
    _create(logged_in_client, "Beperkte reeks", start, "monthly", (start + timedelta(days=90)).isoformat())
    event_id = _event_id(logged_in_client, "Beperkte reeks")
    edit = logged_in_client.get(f"/calendar/events/{event_id}/edit").text
    assert f'value="{(start + timedelta(days=90)).isoformat()}"' in edit
    assert '<option value="monthly" selected>' in edit
    logged_in_client.post(f"/calendar/events/{event_id}/delete")
