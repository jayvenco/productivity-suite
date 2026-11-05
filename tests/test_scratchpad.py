import re

from tests.test_api import _auth_headers, _get_api_token


def test_scratchpad_requires_login(client):
    assert client.get("/scratchpad", follow_redirects=False).status_code == 303


def test_page_is_fullscreen_editor_and_in_navigation(logged_in_client):
    page = logged_in_client.get("/scratchpad").text
    assert 'id="scratchpad-text" data-rich-editor' in page and "js/scratchpad.js" in page
    logged_in_client.post("/settings/navigation", data={"visible": ["tasks", "scratchpad"], "redirect_to": "/account"})
    assert 'href="/scratchpad"' in logged_in_client.get("/tasks").text
    logged_in_client.post("/settings/navigation", data={"visible": ["tasks", "kanban", "mindmap", "notes", "pomodoro", "stickies", "snippets", "calendar", "search", "graph", "inbox", "scratchpad"], "redirect_to": "/account"})


def test_autosave_roundtrip_and_sanitizing(logged_in_client):
    r = logged_in_client.post("/scratchpad", data={"content": "<p>Snelle <b>notitie</b></p><script>x</script>"})
    assert r.status_code == 200 and r.json()["ok"] is True and r.json()["saved_at"]
    page = logged_in_client.get("/scratchpad").text
    assert "&lt;p&gt;Snelle &lt;b&gt;notitie&lt;/b&gt;&lt;/p&gt;" in page  # in de textarea, geëscaped
    assert "script" not in page.split('id="scratchpad-text"')[1].split("</textarea>")[0]
    logged_in_client.post("/scratchpad", data={"content": ""})


def test_scratchpad_api_get_put_append(logged_in_client):
    h = _auth_headers(_get_api_token(logged_in_client))
    c = logged_in_client
    assert c.put("/api/v1/scratchpad", json={"content": "<p>eerste</p>"}, headers=h).json()["content"] == "<p>eerste</p>"
    appended = c.post("/api/v1/scratchpad/append", json={"text": "tweede\nderde & vierde"}, headers=h).json()
    assert appended["content"] == "<p>eerste</p><p>tweede</p><p>derde &amp; vierde</p>"
    assert c.get("/api/v1/scratchpad", headers=h).json()["content"] == appended["content"]
    assert c.post("/api/v1/scratchpad/append", json={"text": "  "}, headers=h).status_code == 400
    c.put("/api/v1/scratchpad", json={"content": ""}, headers=h)


def test_font_and_size_are_saved_and_applied(logged_in_client):
    page = logged_in_client.get("/scratchpad").text
    assert 'id="scratchpad-font"' in page and 'id="scratchpad-size"' in page and 'value="georgia"' in page

    r = logged_in_client.post("/scratchpad/settings", data={"font_family": "georgia", "font_size": "24"})
    assert r.json() == {"ok": True, "font_family": "georgia", "font_size": 24}
    page = logged_in_client.get("/scratchpad").text
    assert re.search(r'<option value="georgia"[^>]*selected', page) and re.search(r'<option value="24"[^>]*selected', page)

    # onbekende waarden worden genegeerd
    again = logged_in_client.post("/scratchpad/settings", data={"font_family": "nepfont", "font_size": "999"}).json()
    assert again["font_family"] == "georgia" and again["font_size"] == 24
    logged_in_client.post("/scratchpad/settings", data={"font_family": "system", "font_size": "16"})
