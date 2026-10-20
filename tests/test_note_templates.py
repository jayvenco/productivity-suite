import json
import re

from app.database import SessionLocal
from app.models.calendar_event import CalendarEvent
from app.models.note import Note
from app.models.note_template import NoteModule, NoteTemplate
from app.models.task import Task


def _template_id(name):
    with SessionLocal() as db:
        return db.query(NoteTemplate).filter(NoteTemplate.name == name).first().id


def _note_by_title(title):
    with SessionLocal() as db:
        note = db.query(Note).filter(Note.title == title).order_by(Note.id.desc()).first()
        note.tag_names = [t.name for t in note.tags]  # nu laden, de sessie sluit hierna
        return note


def test_templates_require_login(client):
    assert client.get("/notes/templates", follow_redirects=False).status_code == 303


def test_library_lists_builtin_templates_by_category_and_search(logged_in_client):
    page = logged_in_client.get("/notes/templates").text
    for name in ["Vergadernotulen", "Weekplanning", "Klein project", "Stappenplan", "Rollen en verantwoordelijkheden"]:
        assert name in page
    assert "Vergaderen &amp; communicatie" in page

    filtered = logged_in_client.get("/notes/templates?q=weekplan").text
    assert "Weekplanning" in filtered and "Vergadernotulen" not in filtered
    by_cat = logged_in_client.get("/notes/templates?category=Planning").text
    assert "Weekplanning" in by_cat and "Klein project" not in by_cat


def test_preview_and_use_form(logged_in_client):
    tid = _template_id("Vergadernotulen")
    preview = logged_in_client.get(f"/notes/templates/{tid}/preview").text
    assert "Actiepunten" in preview and "Deelnemers" in preview
    form = logged_in_client.get(f"/notes/templates/{tid}/use").text
    assert 'name="m0__participants"' in form and "data-add-row" in form


def test_create_note_from_template_with_tasks_links_and_provenance(logged_in_client):
    tid = _template_id("Vergadernotulen")
    with SessionLocal() as db:
        existing = Task(user_id=1, title="Bestaande taak voor link")
        db.add(existing)
        db.commit()
        existing_id = existing.id
        tasks_before = db.query(Task).count()

    response = logged_in_client.post(
        f"/notes/templates/{tid}/use",
        data={
            "title": "Sprintoverleg",
            "m0__title": "Sprintoverleg",
            "m0__participants": "Anna\nBen <script>x</script>",
            "m0__purpose": "Afstemmen",
            "m1__r0__text": "Voortgang bespreken", "m1__r0__minutes": "10",
            "m4__r0__text": "Offerte sturen", "m4__r0__owner": "Anna", "m4__r0__due": "2030-05-01",
            "m4__r1__text": "Bestaande actie", "m4__r1__task": str(existing_id),
            "m4__create_tasks": "1",
            "m5__include": "1",  # open vragen mee; volgende vergadering (m6) niet
            "m5__r0__text": "Wie levert de data?",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303 and "/edit" in response.headers["location"]

    note = _note_by_title("Sprintoverleg")
    assert note.template_id == tid and note.template_version == 1 and note.template_name == "Vergadernotulen"
    assert "Anna<br>Ben" in note.content and "<script>" not in note.content
    assert "Voortgang bespreken" in note.content and "(10 min)" in note.content
    assert "Wie levert de data?" in note.content
    assert "Volgende vergadering" not in note.content  # optionele module overgeslagen
    assert "meeting" in note.tag_names

    with SessionLocal() as db:
        assert db.query(Task).count() == tasks_before + 1  # alleen "Offerte sturen" is nieuw
        created = db.query(Task).filter(Task.title == "Offerte sturen").one()
        assert str(created.deadline) == "2030-05-01"
        assert f'/tasks/{created.id}/edit' in note.content and f'/tasks/{existing_id}/edit' in note.content
        assert note.content.count('Offerte sturen') == 1  # link i.p.v. tekst + link
        db.delete(created)
        db.delete(db.get(Task, existing_id))
        db.commit()


def test_milestones_can_create_calendar_events(logged_in_client):
    tid = _template_id("Klein project")
    logged_in_client.post(
        f"/notes/templates/{tid}/use",
        data={"title": "Website", "m0__name": "Website", "m1__r0__text": "Livegang", "m1__r0__due": "2031-01-15",
              "m1__create_events": "1"},
    )
    with SessionLocal() as db:
        event = db.query(CalendarEvent).filter(CalendarEvent.title == "Livegang").one()
        assert str(event.event_date) == "2031-01-15"
        db.delete(event)
        db.commit()


def test_required_field_is_enforced_and_variables_resolve(logged_in_client):
    tid = _template_id("Klein project")
    bad = logged_in_client.post(f"/notes/templates/{tid}/use", data={"title": "Zonder naam", "m0__name": ""})
    assert bad.status_code == 400

    weekly = _template_id("Weekplanning")
    form = logged_in_client.get(f"/notes/templates/{weekly}/use").text
    assert re.search(r'value="Week \d+"', form)  # {{week}} opgelost


def test_template_edit_bumps_version_and_does_not_touch_existing_notes(logged_in_client):
    with SessionLocal() as db:
        text_module = db.query(NoteModule).filter(NoteModule.key == "notes").one().id
        check_module = db.query(NoteModule).filter(NoteModule.key == "checklist").one().id

    modules = [{"module_id": text_module, "title": "Intro {{date}}", "optional": False, "default_content": "", "config": ""}]
    logged_in_client.post(
        "/notes/templates",
        data={"name": "Eigen sjabloon", "category": "Eigen", "icon": "⭐", "tags": "eigen", "modules_json": json.dumps(modules)},
    )
    tid = _template_id("Eigen sjabloon")
    logged_in_client.post(f"/notes/templates/{tid}/use", data={"title": "Uit eigen", "m0__text": "Hallo"})
    old = _note_by_title("Uit eigen")
    old_content = old.content
    assert "Intro" in old_content and old.template_version == 1

    modules.append({"module_id": check_module, "title": "Nieuw blok", "optional": True, "default_content": "", "config": ""})
    logged_in_client.post(f"/notes/templates/{tid}", data={"name": "Eigen sjabloon v2", "modules_json": json.dumps(modules)})
    with SessionLocal() as db:
        assert db.get(NoteTemplate, tid).version == 2
        assert db.get(Note, old.id).content == old_content  # zelfstandig

    logged_in_client.post(f"/notes/templates/{tid}/delete")
    with SessionLocal() as db:
        survivor = db.get(Note, old.id)
        assert survivor is not None and survivor.template_id is None and survivor.template_name == "Eigen sjabloon"
        db.delete(survivor)
        db.commit()


def test_builtins_are_protected_duplicate_and_restore(logged_in_client):
    tid = _template_id("Stappenplan")
    assert logged_in_client.post(f"/notes/templates/{tid}/delete").status_code == 400
    assert logged_in_client.get(f"/notes/templates/{tid}/edit").status_code == 400

    dup = logged_in_client.post(f"/notes/templates/{tid}/duplicate", follow_redirects=False)
    assert dup.status_code == 303
    copy_id = int(dup.headers["location"].split("/")[3])
    assert logged_in_client.get(f"/notes/templates/{copy_id}/edit").status_code == 200
    assert logged_in_client.post(f"/notes/templates/{copy_id}/delete", follow_redirects=False).status_code == 303

    with SessionLocal() as db:
        db.query(NoteTemplate).filter(NoteTemplate.builtin_key == "checklist").delete()
        db.commit()
    assert logged_in_client.post("/notes/templates/restore-builtins", follow_redirects=False).status_code == 303
    assert "Checklist" in logged_in_client.get("/notes/templates").text


def test_invalid_modules_json_rejected_and_preview_fragment(logged_in_client):
    assert logged_in_client.post("/notes/templates", data={"name": "Fout", "modules_json": "geen json"}).status_code == 400
    assert logged_in_client.post(
        "/notes/templates", data={"name": "Fout", "modules_json": json.dumps([{"module_id": 99999}])}
    ).status_code == 400

    with SessionLocal() as db:
        module_id = db.query(NoteModule).filter(NoteModule.key == "checklist").one().id
    fragment = logged_in_client.post(
        "/notes/templates/preview",
        data={"name": "X", "modules_json": json.dumps([{"module_id": module_id, "title": "Mijn lijst"}])},
    )
    assert fragment.status_code == 200 and "<h2>Mijn lijst</h2>" in fragment.text
