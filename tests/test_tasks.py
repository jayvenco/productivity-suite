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


def test_deadline_warning_badge_for_near_deadline(logged_in_client):
    near_deadline = (date.today() + timedelta(days=2)).isoformat()
    logged_in_client.post(
        "/tasks",
        data={"title": "Bijna deadline", "description": "", "deadline": near_deadline, "tags": ""},
    )
    listing = logged_in_client.get("/tasks").text
    assert "badge-warning" in listing


def test_task_card_shows_description_preview(logged_in_client):
    logged_in_client.post(
        "/tasks",
        data={
            "title": "Met beschrijving",
            "description": "Dit is een langere beschrijving die afgekapt moet worden",
            "deadline": "",
            "tags": "",
        },
    )
    listing = logged_in_client.get("/tasks").text
    assert '<span class="task-card-preview">Dit is een langere b…</span>' in listing


def test_task_card_hides_preview_without_description(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Kaart zonder beschrijving", "description": "", "deadline": "", "tags": ""}
    )
    listing = logged_in_client.get("/tasks").text
    # Andere taken in dezelfde lijst kunnen wél een beschrijving (en dus preview)
    # hebben -- scope de check tot de kaart van déze taak, niet de hele pagina.
    title_idx = listing.index("Kaart zonder beschrijving")
    card_start = listing.rindex('<div class="task-card', 0, title_idx)
    next_card = listing.find('<div class="task-card', title_idx)
    card_html = listing[card_start : next_card if next_card != -1 else len(listing)]
    assert "task-card-preview" not in card_html


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


def test_filter_by_single_tag(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Werktaak", "description": "", "deadline": "", "tags": "werk"})
    logged_in_client.post("/tasks", data={"title": "Privetaak", "description": "", "deadline": "", "tags": "prive"})

    filtered = logged_in_client.get("/tasks?tags=werk").text
    assert "Werktaak" in filtered
    assert "Privetaak" not in filtered


def test_filter_by_multiple_tags_is_or(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Werktaak", "description": "", "deadline": "", "tags": "werk"})
    logged_in_client.post("/tasks", data={"title": "Privetaak", "description": "", "deadline": "", "tags": "prive"})
    logged_in_client.post("/tasks", data={"title": "Sporttaak", "description": "", "deadline": "", "tags": "sport"})

    filtered = logged_in_client.get("/tasks?tags=werk&tags=prive").text
    assert "Werktaak" in filtered
    assert "Privetaak" in filtered
    assert "Sporttaak" not in filtered


def test_tag_filter_checkboxes_listed_and_checked(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Werktaak", "description": "", "deadline": "", "tags": "werk"})

    page = logged_in_client.get("/tasks?tags=werk").text
    assert 'class="task-tag-filter"' in page
    assert 'name="tags" value="werk"' in page
    checkbox = re.search(r'<input type="checkbox" name="tags" value="werk"[^>]*>', page).group(0)
    assert "checked" in checkbox


def test_task_card_has_no_tag_color_tint(logged_in_client):
    logged_in_client.post(
        "/tasks", data={"title": "Geen tint", "description": "", "deadline": "", "tags": "werk"}
    )
    listing = logged_in_client.get("/tasks").text
    # De kaart zelf mag geen inline achtergrondkleur krijgen op basis van de tag --
    # de tag-badge en de filter-checkbox mogen wel gekleurd zijn.
    assert not re.search(r'class="task-card[^"]*"[^>]*style="[^"]*hsla', listing)


def test_task_group_headings_are_toggle_buttons(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Werktaak", "description": "", "deadline": "", "tags": "werk"})

    listing = logged_in_client.get("/tasks?group_by=tag").text
    assert 'data-group-toggle="werk"' in listing
    assert 'data-group-block="werk"' in listing


def _task_id_for_title(html: str, title: str) -> str:
    """Zoekt het taak-id horend bij deze titel. Zoekt terug vanaf de titel naar de
    dichtstbijzijnde voorgaande edit-link, i.p.v. voorwaarts (dat zou per ongeluk
    het id van een eerdere kaart kunnen pakken als er meerdere zijn)."""
    idx = html.index(title)
    matches = list(re.finditer(r'href="/tasks/(\d+)/edit"', html[:idx]))
    assert matches, f"Taak met titel {title!r} niet gevonden"
    return matches[-1].group(1)


def test_toggle_done_marks_task_done_and_back(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Snel afvinken", "description": "", "deadline": "", "tags": ""})
    listing = logged_in_client.get("/tasks").text
    task_id = _task_id_for_title(listing, "Snel afvinken")

    response = logged_in_client.post(f"/tasks/{task_id}/toggle-done", follow_redirects=False)
    assert response.status_code == 303

    after_done = logged_in_client.get("/tasks").text
    assert "task-card-done" in after_done

    logged_in_client.post(f"/tasks/{task_id}/toggle-done")
    after_reopen = logged_in_client.get("/tasks").text
    assert "task-card-done" not in after_reopen


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


def test_task_card_whole_card_is_clickable_to_edit(logged_in_client):
    logged_in_client.post("/tasks", data={"title": "Klikbare kaart", "description": "", "deadline": "", "tags": ""})
    listing = logged_in_client.get("/tasks").text
    task_id = _task_id_for_title(listing, "Klikbare kaart")
    assert f'data-href="/tasks/{task_id}/edit"' in listing
