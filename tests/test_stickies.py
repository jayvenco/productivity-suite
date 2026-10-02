import re
from datetime import UTC, datetime, timedelta

from app.database import SessionLocal
from app.models.sticky import Sticky


def _id_for(client, text):
    html = client.get("/stickies").text
    idx = html.index(text)
    return re.findall(r'action="/stickies/(\d+)"', html[:idx])[-1]


def test_stickies_requires_login(client):
    assert client.get("/stickies", follow_redirects=False).status_code == 303


def test_create_sticky_with_color_tag_and_temp(logged_in_client):
    r = logged_in_client.post(
        "/stickies",
        data={"content": "Melk kopen", "color": "pink", "tags": "boodschappen", "is_temp": "true"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    page = logged_in_client.get("/stickies").text
    assert "Melk kopen" in page
    assert "sticky-pink" in page
    assert 'value="true" class="round-checkbox" checked' in page  # temp staat achter het ⚙-knopje
    assert "TEMP" not in page  # geen label meer op het briefje zelf
    assert 'href="/stickies?tags=boodschappen"' in page

    sid = _id_for(logged_in_client, "Melk kopen")
    logged_in_client.post(f"/stickies/{sid}/delete")


def test_update_color_via_fetch_and_invalid_color_falls_back(logged_in_client):
    logged_in_client.post("/stickies", data={"content": "Kleurtest", "color": "blue"})
    sid = _id_for(logged_in_client, "Kleurtest")

    r = logged_in_client.post(
        f"/stickies/{sid}",
        data={"content": "Kleurtest", "color": "green", "tags": ""},
        headers={"X-Requested-With": "fetch"},
    )
    assert r.status_code == 204
    with SessionLocal() as db:
        assert db.get(Sticky, int(sid)).color == "green"

    logged_in_client.post(f"/stickies/{sid}", data={"content": "Kleurtest", "color": "zwart", "tags": ""})
    with SessionLocal() as db:
        assert db.get(Sticky, int(sid)).color == "yellow"

    logged_in_client.post(f"/stickies/{sid}/delete")


def test_filter_by_tag(logged_in_client):
    logged_in_client.post("/stickies", data={"content": "Werk-sticky", "tags": "werkfilter"})
    logged_in_client.post("/stickies", data={"content": "Prive-sticky", "tags": "privefilter"})
    page = logged_in_client.get("/stickies?tags=werkfilter").text
    assert "Werk-sticky" in page and "Prive-sticky" not in page
    for text in ["Werk-sticky", "Prive-sticky"]:
        logged_in_client.post(f"/stickies/{_id_for(logged_in_client, text)}/delete")


def test_expired_temp_sticky_is_deleted_but_normal_one_survives(logged_in_client):
    logged_in_client.post("/stickies", data={"content": "Verlopen temp", "is_temp": "true"})
    logged_in_client.post("/stickies", data={"content": "Oude gewone sticky"})
    old = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=8)
    with SessionLocal() as db:
        for s in db.query(Sticky).filter(Sticky.content.in_(["Verlopen temp", "Oude gewone sticky"])):
            s.created_at = old
        db.commit()

    page = logged_in_client.get("/stickies").text
    assert "Verlopen temp" not in page
    assert "Oude gewone sticky" in page
    logged_in_client.post(f"/stickies/{_id_for(logged_in_client, 'Oude gewone sticky')}/delete")
