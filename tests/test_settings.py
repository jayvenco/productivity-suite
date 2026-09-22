def test_set_theme(logged_in_client):
    response = logged_in_client.post(
        "/settings/theme", data={"theme": "nexmail", "redirect_to": "/tasks"}, follow_redirects=False
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="nexmail"' in page


def test_set_macos_light_theme(logged_in_client):
    response = logged_in_client.post(
        "/settings/theme", data={"theme": "macos-light", "redirect_to": "/tasks"}, follow_redirects=False
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="macos-light"' in page


def test_set_anchor_theme(logged_in_client):
    response = logged_in_client.post(
        "/settings/theme", data={"theme": "anchor", "redirect_to": "/tasks"}, follow_redirects=False
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="anchor"' in page

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post("/settings/theme", data={"theme": "dracula", "redirect_to": "/tasks"})


def test_set_anchor_solid_theme(logged_in_client):
    response = logged_in_client.post(
        "/settings/theme", data={"theme": "anchor-solid", "redirect_to": "/tasks"}, follow_redirects=False
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-theme="anchor-solid"' in page

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post("/settings/theme", data={"theme": "dracula", "redirect_to": "/tasks"})


def test_set_dm_sans_and_playfair_display_fonts(logged_in_client):
    for font_id in ["dm-sans", "playfair-display"]:
        response = logged_in_client.post(
            "/settings/appearance",
            data={
                "font_family": font_id,
                "font_size": "14",
                "density": "comfortable",
                "background": "none",
                "background_opacity": "30",
                "redirect_to": "/tasks",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        page = logged_in_client.get("/tasks").text
        assert f'data-font="{font_id}"' in page

    # Terugzetten voor eventuele volgende tests in deze module.
    logged_in_client.post(
        "/settings/appearance",
        data={
            "font_family": "system",
            "font_size": "14",
            "density": "comfortable",
            "background": "none",
            "background_opacity": "30",
            "redirect_to": "/tasks",
        },
    )


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


def test_set_appearance_accepts_background(logged_in_client):
    response = logged_in_client.post(
        "/settings/appearance",
        data={
            "font_family": "system",
            "font_size": "14",
            "density": "comfortable",
            "background": "mountains",
            "background_opacity": "45",
            "redirect_to": "/tasks",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-background="mountains"' in page
    assert "--background-opacity: 0.45" in page


def test_set_appearance_defaults_background_to_none(logged_in_client):
    response = logged_in_client.post(
        "/settings/appearance",
        data={"font_family": "system", "font_size": "14", "density": "comfortable", "redirect_to": "/tasks"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = logged_in_client.get("/tasks").text
    assert 'data-background="none"' in page


def test_set_appearance_ignores_unknown_background_and_out_of_range_opacity(logged_in_client):
    logged_in_client.post(
        "/settings/appearance",
        data={
            "font_family": "system",
            "font_size": "14",
            "density": "comfortable",
            "background": "space",
            "background_opacity": "40",
            "redirect_to": "/tasks",
        },
    )
    logged_in_client.post(
        "/settings/appearance",
        data={
            "font_family": "system",
            "font_size": "14",
            "density": "comfortable",
            "background": "onbekend",
            "background_opacity": "999",
            "redirect_to": "/tasks",
        },
    )

    page = logged_in_client.get("/tasks").text
    assert 'data-background="space"' in page
    assert "--background-opacity: 0.4" in page


def test_account_page_lists_background_options(logged_in_client):
    page = logged_in_client.get("/account").text
    assert "Achtergrond" in page
    assert "Natuur" in page
    assert "Bergen" in page
    assert "Heelal" in page
