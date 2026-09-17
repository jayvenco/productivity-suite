import re
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
    assert "rgb(" in listing


def test_sort_by_title(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Zebra", "description": "", "deadline": "", "tags": ""})
    logged_in_client.post("/tasks", data={"title": "Aap", "description": "", "deadline": "", "tags": ""})

    listing = logged_in_client.get("/tasks?sort=title").text
    assert listing.index("Aap") < listing.index("Zebra")


def test_group_by_tag_creates_group_headings(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Werktaak", "description": "", "deadline": "", "tags": "werk"}
    )
    logged_in_client.post(
        "/tasks", data={"title": "Privetaak", "description": "", "deadline": "", "tags": "prive"}
    )
    logged_in_client.post(
        "/tasks", data={"title": "Losse taak", "description": "", "deadline": "", "tags": ""}
    )

    listing = logged_in_client.get("/tasks?group_by=tag").text
    assert "task-group-heading" in listing
    assert "Werktaak" in listing
    assert "Privetaak" in listing
    assert "Zonder tag" in listing
    assert "Losse taak" in listing


def test_each_tag_gets_a_distinct_color(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Kleurtest", "description": "", "deadline": "", "tags": "alfa, beta"}
    )
    listing = logged_in_client.get("/tasks").text
    assert "hsl(" in listing
    # Twee verschillende tags -> minstens twee verschillende hue-waarden in de badges.
    hues = set(re.findall(r"hsl\((\d+),", listing))
    assert len(hues) >= 2


def _task_id_for_title(html: str, title: str) -> str:
    match = re.search(rf'/tasks/(\d+)/edit">{re.escape(title)}</a>', html)
    assert match, f"Taak met titel {title!r} niet gevonden"
    return match.group(1)


def test_toggle_done_marks_task_done_and_back(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Snel afvinken", "description": "", "deadline": "", "tags": ""})
    listing = logged_in_client.get("/tasks").text
    task_id = _task_id_for_title(listing, "Snel afvinken")

    response = logged_in_client.post(f"/tasks/{task_id}/toggle-done", follow_redirects=False)
    assert response.status_code == 303

    after_done = logged_in_client.get("/tasks").text
    assert "task-row-done" in after_done

    logged_in_client.post(f"/tasks/{task_id}/toggle-done")
    after_reopen = logged_in_client.get("/tasks").text
    assert "task-row-done" not in after_reopen


def test_toggle_done_preserves_sort_and_group_by(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Behoud filter", "description": "", "deadline": "", "tags": "werk"}
    )
    listing = logged_in_client.get("/tasks?sort=title&group_by=tag").text
    task_id = _task_id_for_title(listing, "Behoud filter")

    response = logged_in_client.post(
        f"/tasks/{task_id}/toggle-done",
        data={"sort": "title", "group_by": "tag"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    location = response.headers["location"]
    assert "sort=title" in location
    assert "group_by=tag" in location

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post(f"/tasks/{task_id}/toggle-done")


def test_tables_use_fixed_layout_for_stable_alignment(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Uitlijning", "description": "", "deadline": "", "tags": "werk"})
    listing = logged_in_client.get("/tasks?status_filter=todo").text
    assert "tasks-table" in listing
    assert 'col class="col-title"' in listing
