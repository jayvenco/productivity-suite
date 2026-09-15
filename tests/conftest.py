import os
import tempfile

import pytest

_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEFAULT_USERNAME"] = "admin"
os.environ["DEFAULT_PASSWORD"] = "testpass"

from app.main import app  # noqa: E402  (moet na het zetten van env vars gebeuren)


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def logged_in_client(client):
    client.post("/login", data={"username": "admin", "password": "testpass"})
    return client
