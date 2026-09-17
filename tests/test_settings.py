def test_set_theme(logged_in_client):
    response = logged_in_client.post(
        "/settings/theme", data={"theme": "nexmail", "redirect_to": "/tasks"}, follow_redirects=False
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="nexmail"' in page


def test_set_theme_ignores_unknown_value(logged_in_client):
    logged_in_client.post("/settings/theme", data={"theme": "nexmail", "redirect_to": "/tasks"})
    logged_in_client.post("/settings/theme", data={"theme": "geen-bestaand-thema", "redirect_to": "/tasks"})

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="nexmail"' in page


def test_set_appearance(logged_in_client):
    response = logged_in_client.post(
        "/settings/appearance",
        data={"font_family": "inter", "font_size": "16", "density": "compact", "redirect_to": "/tasks"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-font="inter"' in page
    assert 'data-density="compact"' in page
    assert "--font-size-base: 16px" in page


def test_set_appearance_ignores_unknown_values(logged_in_client):
    logged_in_client.post(
        "/settings/appearance",
        data={"font_family": "inter", "font_size": "16", "density": "compact", "redirect_to": "/tasks"},
    )
    logged_in_client.post(
        "/settings/appearance",
        data={"font_family": "onbekend", "font_size": "999", "density": "onbekend", "redirect_to": "/tasks"},
    )

    page = logged_in_client.get("/tasks").text
    assert 'data-font="inter"' in page
    assert 'data-density="compact"' in page
    assert "--font-size-base: 16px" in page


def test_account_page_lists_appearance_options(logged_in_client):
    page = logged_in_client.get("/account").text
    assert "Weergave" in page
    assert "Inter" in page
    assert "Compact" in page
    assert "Hack" in page


def test_set_appearance_accepts_monospace_font(logged_in_client):
    response = logged_in_client.post(
        "/settings/appearance",
        data={"font_family": "hack", "font_size": "14", "density": "comfortable", "redirect_to": "/tasks"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-font="hack"' in page
