def test_redirects_to_login_when_anonymous(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_wrong_password(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_success_redirects_home(client):
    response = client.post(
        "/login", data={"username": "admin", "password": "testpass"}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "ps_session" in response.cookies
