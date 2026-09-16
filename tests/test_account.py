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
