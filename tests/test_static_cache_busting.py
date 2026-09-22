from app.templating import static_url


def test_static_url_appends_mtime_version():
    url = static_url("css/app.css")
    assert url.startswith("/static/css/app.css?v=")
    version = url.split("?v=")[1]
    assert version.isdigit()
    assert int(version) > 0


def test_static_url_changes_when_file_mtime_changes(tmp_path, monkeypatch):
    from app import templating

    fake_static = tmp_path / "static"
    (fake_static / "css").mkdir(parents=True)
    css_file = fake_static / "css" / "app.css"
    css_file.write_text("body {}")

    monkeypatch.setattr(templating, "_STATIC_DIR", fake_static)

    first = static_url("css/app.css")
    os_utime_forward(css_file)
    second = static_url("css/app.css")

    assert first != second


def os_utime_forward(path):
    import os
    import time

    future = time.time() + 5
    os.utime(path, (future, future))


def test_static_url_missing_file_falls_back_to_zero(tmp_path, monkeypatch):
    from app import templating

    monkeypatch.setattr(templating, "_STATIC_DIR", tmp_path)
    assert static_url("does/not/exist.css") == "/static/does/not/exist.css?v=0"


def test_page_references_static_url_with_version_query(logged_in_client):
    page = logged_in_client.get("/tasks").text
    assert '/static/css/app.css?v=' in page
    assert '/static/js/tasks-list.js?v=' in page
