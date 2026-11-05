import re
from pathlib import Path

from app.database import SessionLocal
from app.models.inbox import InboxItem

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_manifest_is_public_and_installable(client):
    r = client.get("/manifest.webmanifest")  # geen login nodig
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/manifest+json")
    m = r.json()
    assert m["display"] == "standalone" and m["start_url"] == "/" and m["scope"] == "/"
    sizes = {(i["sizes"], i["purpose"]) for i in m["icons"]}
    assert ("192x192", "any") in sizes and ("512x512", "any") in sizes and ("512x512", "maskable") in sizes
    for icon in m["icons"]:
        assert (STATIC / icon["src"].removeprefix("/static/")).exists(), icon["src"]
    assert m["share_target"]["action"] == "/inbox/share" and m["share_target"]["method"] == "POST"
    assert {s["url"] for s in m["shortcuts"]} >= {"/inbox", "/scratchpad"}


def test_service_worker_and_offline_page_are_public(client):
    sw = client.get("/service-worker.js")
    assert sw.status_code == 200 and "javascript" in sw.headers["content-type"]
    assert sw.headers["cache-control"] == "no-cache" and sw.headers["service-worker-allowed"] == "/"
    assert "/offline" in sw.text and "ps-static-" in sw.text
    offline = client.get("/offline")
    assert offline.status_code == 200 and "Je bent offline" in offline.text


def test_pages_link_manifest_and_register_worker(logged_in_client):
    page = logged_in_client.get("/tasks").text
    assert 'rel="manifest" href="/manifest.webmanifest"' in page
    assert 'name="theme-color"' in page and "apple-touch-icon" in page and "js/pwa-register.js" in page
    assert re.search(r"<script>", page) is None  # geen inline scripts (zie de XSS-test)


def test_share_target_creates_inbox_item(logged_in_client):
    r = logged_in_client.post(
        "/inbox/share",
        data={"title": "Handige pagina", "text": "Lees dit later & bewaar", "url": "https://example.com/artikel"},
        follow_redirects=False,
    )
    assert r.status_code == 303 and r.headers["location"] == "/inbox"
    with SessionLocal() as db:
        item = db.query(InboxItem).filter(InboxItem.text.contains("Handige pagina")).one()
        assert "<p>Handige pagina</p>" in item.text and "&amp; bewaar" in item.text and "example.com/artikel" in item.text
        db.delete(item)
        db.commit()


def test_share_target_requires_login():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as anonymous:  # verse client, zonder sessie-cookie
        r = anonymous.post("/inbox/share", data={"text": "x"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_share_target_ignores_empty_share(logged_in_client):
    before = logged_in_client.get("/inbox/count").json()["count"]
    logged_in_client.post("/inbox/share", data={"title": " ", "text": "", "url": ""})
    assert logged_in_client.get("/inbox/count").json()["count"] == before
