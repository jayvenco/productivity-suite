from unittest.mock import AsyncMock, MagicMock, patch

import httpx


def _fake_whisper_client(*, text=None, error=None):
    fake_client = AsyncMock()
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = False
    if error is not None:
        fake_client.post.side_effect = error
    else:
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"text": text}
        fake_client.post.return_value = fake_response
    return fake_client


def test_transcribe_requires_login(client):
    response = client.post(
        "/voice/transcribe",
        files={"audio": ("test.webm", b"fake-audio", "audio/webm")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_transcribe_rejects_empty_audio(logged_in_client):
    response = logged_in_client.post("/voice/transcribe", files={"audio": ("test.webm", b"", "audio/webm")})
    assert response.status_code == 400


def test_transcribe_returns_text_from_whisper_service(logged_in_client):
    fake_client = _fake_whisper_client(text="Hallo wereld")
    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/transcribe", files={"audio": ("test.webm", b"fake-audio-bytes", "audio/webm")}
        )
    assert response.status_code == 200
    assert response.json() == {"text": "Hallo wereld"}


def test_transcribe_handles_unreachable_whisper_service(logged_in_client):
    fake_client = _fake_whisper_client(error=httpx.ConnectError("boom"))
    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/transcribe", files={"audio": ("test.webm", b"fake-audio-bytes", "audio/webm")}
        )
    assert response.status_code == 503


def test_transcribe_surfaces_whisper_service_error_response(logged_in_client):
    fake_response = MagicMock()
    fake_response.status_code = 404
    fake_response.text = "model not found"
    fake_client = AsyncMock()
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = False
    fake_client.post.return_value = fake_response

    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/transcribe", files={"audio": ("test.webm", b"fake-audio-bytes", "audio/webm")}
        )
    assert response.status_code == 502
    assert "404" in response.json()["detail"]


def _fake_models_client(*, status_code=200, model_ids=None, error=None):
    fake_client = AsyncMock()
    fake_client.__aenter__.return_value = fake_client
    fake_client.__aexit__.return_value = False
    if error is not None:
        fake_client.get.side_effect = error
    else:
        fake_response = MagicMock()
        fake_response.status_code = status_code
        fake_response.json.return_value = {"data": [{"id": m} for m in (model_ids or [])]}
        fake_client.get.return_value = fake_response
    return fake_client


def test_test_connection_reports_valid_when_model_is_loaded(logged_in_client):
    fake_client = _fake_models_client(model_ids=["Systran/faster-whisper-base", "other-model"])
    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/test-connection",
            data={"whisper_service_url": "http://whisper:8000", "whisper_model": "Systran/faster-whisper-base"},
        )
    data = response.json()
    assert data["valid"] is True
    assert "Systran/faster-whisper-base" in data["message"]


def test_test_connection_reports_missing_model(logged_in_client):
    fake_client = _fake_models_client(model_ids=["other-model"])
    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/test-connection",
            data={"whisper_service_url": "http://whisper:8000", "whisper_model": "does-not-exist"},
        )
    data = response.json()
    assert data["valid"] is False
    assert "other-model" in data["message"]


def test_test_connection_handles_unreachable_service(logged_in_client):
    fake_client = _fake_models_client(error=httpx.ConnectError("boom"))
    with patch("app.routers.voice.httpx.AsyncClient", return_value=fake_client):
        response = logged_in_client.post(
            "/voice/test-connection",
            data={"whisper_service_url": "http://onbereikbaar:8000", "whisper_model": "x"},
        )
    data = response.json()
    assert data["valid"] is False
    assert "onbereikbaar" in data["message"]
