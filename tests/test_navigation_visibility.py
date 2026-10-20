import re


def _nav_labels(client) -> list[str]:
    html = client.get("/tasks").text
    sidebar = html[html.index('class="sidebar"'): html.index('class="theme-switcher"')]
    return re.findall(r'class="nav-item[^"]*"[^>]*><span class="nav-icon">[^<]*</span>([^<]+)<', sidebar)


def _set_visible(client, keys):
    client.post("/settings/navigation", data={"visible": keys, "redirect_to": "/account"})


ALL = ["tasks", "kanban", "mindmap", "notes", "pomodoro", "stickies", "snippets", "calendar", "search", "graph", "stats"]


def test_statistics_hidden_by_default_and_toggle_shows_it(logged_in_client):
    _set_visible(logged_in_client, [k for k in ALL if k != "stats"])
    assert "Statistieken" not in _nav_labels(logged_in_client)

    _set_visible(logged_in_client, ALL)
    assert "Statistieken" in _nav_labels(logged_in_client)
    # terugzetten: standaard staat Statistieken uit
    _set_visible(logged_in_client, [k for k in ALL if k != "stats"])


def test_any_module_can_be_hidden_and_setting_persists(logged_in_client):
    _set_visible(logged_in_client, [k for k in ALL if k not in ("stickies", "mindmap", "stats")])
    labels = _nav_labels(logged_in_client)
    assert "Stickies" not in labels and "Mindmap" not in labels and "Taken" in labels

    # blijft bewaard bij een volgend verzoek en staat aangevinkt/uit op de accountpagina
    page = logged_in_client.get("/account").text
    assert re.search(r'name="visible" value="stickies"[^>]*>', page)
    assert "checked" not in re.search(r'name="visible" value="stickies"[^>]*>', page).group(0)
    assert "checked" in re.search(r'name="visible" value="tasks"[^>]*>', page).group(0)

    _set_visible(logged_in_client, [k for k in ALL if k != "stats"])


def test_at_least_one_module_must_stay_visible(logged_in_client):
    _set_visible(logged_in_client, [k for k in ALL if k != "stats"])
    logged_in_client.post("/settings/navigation", data={"redirect_to": "/account"})  # niets aangevinkt
    assert "Taken" in _nav_labels(logged_in_client)


def test_hidden_module_is_still_reachable_by_url(logged_in_client):
    assert logged_in_client.get("/stats").status_code == 200


def test_daily_task_has_no_star_badge_but_keeps_daily_class(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Check-dagtaak", "daily_task": "true", "description": "", "deadline": "", "tags": ""})
    page = logged_in_client.get("/tasks").text
    card_start = page.rindex('<div class="task-card ', 0, page.index("Check-dagtaak"))
    card = page[card_start: page.index("Check-dagtaak")]
    assert "task-card-daily" in card and "daily-task-badge" not in card
    task_id = re.search(r'/tasks/(\d+)/edit"', page[card_start:]).group(1)
    logged_in_client.post(f"/tasks/{task_id}/delete")
