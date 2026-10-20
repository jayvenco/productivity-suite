from __future__ import annotations

import json
import re
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.calendar_event import CalendarEvent
from app.models.note import Note
from app.models.note_template import NoteModule, NoteTemplate, NoteTemplateModule
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.note_template_data import CATEGORIES
from app.services.note_templates import (
    FIELD_TYPES,
    MODULE_TYPES,
    module_columns,
    module_fields,
    render_module,
    resolve_vars,
    seed_builtin_templates,
    variable_context,
)
from app.services.richtext import sanitize_note_html
from app.services.tags import resolve_tags
from app.templating import templates

# Moet vóór de notes-router geregistreerd worden (zie app/main.py): anders vangt
# POST /notes/{note_id} van die router "POST /notes/templates" af met een 422.
router = APIRouter(prefix="/notes/templates", tags=["note-templates"])

_ROW_KEY = re.compile(r"^m(\d+)__r(\d+)__(\w+)$")


def _visible(db: Session, user: User):
    return db.query(NoteTemplate).filter(or_(NoteTemplate.user_id.is_(None), NoteTemplate.user_id == user.id))


def _get_template(db: Session, template_id: int, user: User) -> NoteTemplate:
    template = (
        _visible(db, user)
        .options(selectinload(NoteTemplate.modules).selectinload(NoteTemplateModule.module))
        .filter(NoteTemplate.id == template_id)
        .first()
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Sjabloon niet gevonden")
    return template


def _open_tasks(db: Session, user: User) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.status != TaskStatus.DONE, Task.archived_at.is_(None))
        .order_by(Task.title)
        .limit(300)
        .all()
    )


def _form_modules(template: NoteTemplate, ctx: dict[str, str]) -> list[dict]:
    """Per sjabloonmodule alles wat het invulformulier en de preview nodig hebben, met
    variabelen in titels/standaardwaarden al ingevuld."""
    result = []
    for index, tm in enumerate(template.modules):
        mtype = tm.module.type
        config = tm.effective_config
        fields = []
        for field in module_fields(mtype, config):
            fields.append({**field, "default": resolve_vars(str(field.get("default", "")), ctx)})
        spec = MODULE_TYPES.get(mtype, MODULE_TYPES["text"])
        result.append(
            {
                "index": index,
                "type": mtype,
                "title": resolve_vars(tm.effective_title, ctx),
                "optional": tm.optional,
                "default": resolve_vars(tm.effective_default, ctx),
                "kind": spec["kind"],
                "fields": fields,
                "columns": module_columns(mtype),
                "can_tasks": spec.get("can_tasks", False),
                "can_events": spec.get("can_events", False),
                "config": config,
            }
        )
    return result


def _render_note_html(modules: list[dict], values: dict[int, dict], rows: dict[int, list[dict]], tasks: dict) -> str:
    parts = []
    for module in modules:
        i = module["index"]
        if i not in values:  # niet-opgenomen optionele module
            continue
        parts.append(render_module(module["type"], module["title"], module["config"], values[i], rows.get(i, []), tasks,
                                   module["default"]))
    return sanitize_note_html("".join(parts))


def _preview_html(template: NoteTemplate) -> str:
    ctx = variable_context(template.name)
    modules = _form_modules(template, ctx)
    values = {m["index"]: {f["name"]: f["default"] for f in m["fields"]} for m in modules}
    return _render_note_html(modules, values, {}, {})


# ---- Bibliotheek ----


@router.get("")
def library(
    request: Request,
    q: str = "",
    category: str = "",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = _visible(db, user).options(selectinload(NoteTemplate.modules))
    if category:
        query = query.filter(NoteTemplate.category == category)
    found = query.order_by(NoteTemplate.category, NoteTemplate.name).all()
    needle = q.strip().lower()
    if needle:
        found = [
            t for t in found
            if needle in t.name.lower() or needle in t.description.lower() or needle in t.tags.lower()
        ]
    grouped: dict[str, list[NoteTemplate]] = {}
    for t in found:
        grouped.setdefault(t.category, []).append(t)
    ordered = sorted(grouped.items(), key=lambda kv: (CATEGORIES.index(kv[0]) if kv[0] in CATEGORIES else 99, kv[0]))
    return templates.TemplateResponse(
        request,
        "notes/templates_list.html",
        {"user": user, "groups": ordered, "q": q, "category": category, "categories": CATEGORIES,
         "total": len(found)},
    )


@router.post("/restore-builtins")
def restore_builtins(user: User = Depends(require_user), db: Session = Depends(get_db)):
    seed_builtin_templates(db, reset=True)
    return RedirectResponse("/notes/templates", status_code=303)


# ---- Sjabloon maken / bewerken ----


def _editor_context(user: User, db: Session, template: NoteTemplate | None) -> dict:
    library = db.query(NoteModule).filter(or_(NoteModule.user_id.is_(None), NoteModule.user_id == user.id)).order_by(
        NoteModule.id).all()
    modules = [
        {
            "module_id": tm.module_id,
            "title": tm.title,
            "optional": tm.optional,
            "default_content": tm.default_content,
            "config": tm.config,
            "name": tm.module.name,
            "type": tm.module.type,
        }
        for tm in (template.modules if template else [])
    ]
    return {
        "user": user,
        "template": template,
        "library": [{"id": m.id, "name": m.name, "type": m.type, "kind": MODULE_TYPES.get(m.type, {}).get("kind")}
                    for m in library],
        "modules": modules,
        "categories": CATEGORIES,
        "field_types": FIELD_TYPES,
    }


@router.get("/new")
def new_template_form(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "notes/templates_edit.html", _editor_context(user, db, None))


def _apply_form(db: Session, user: User, template: NoteTemplate, name: str, description: str, category: str, icon: str,
                tags: str, title_pattern: str, modules_json: str) -> None:
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Naam is verplicht")
    try:
        raw = json.loads(modules_json or "[]")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ongeldige modulelijst") from exc
    if not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="Ongeldige modulelijst")

    library = {m.id for m in db.query(NoteModule).filter(or_(NoteModule.user_id.is_(None), NoteModule.user_id == user.id))}
    built = []
    for position, item in enumerate(raw):
        if not isinstance(item, dict) or item.get("module_id") not in library:
            raise HTTPException(status_code=400, detail="Onbekende module in sjabloon")
        config = (item.get("config") or "").strip()
        if config:
            try:
                json.loads(config)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Ongeldige JSON in moduleconfiguratie") from exc
        built.append(
            NoteTemplateModule(
                module_id=item["module_id"],
                position=position,
                title=str(item.get("title") or "")[:150],
                optional=bool(item.get("optional")),
                default_content=str(item.get("default_content") or ""),
                config=config,
            )
        )
    template.name = name[:120]
    template.description = description
    template.category = category.strip() or CATEGORIES[-1]
    template.icon = icon.strip()[:10] or "📝"
    template.tags = tags.strip()
    template.title_pattern = title_pattern.strip() or "{{title}}"
    template.modules = built


@router.post("")
def create_template(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    icon: str = Form("📝"),
    tags: str = Form(""),
    title_pattern: str = Form("{{title}}"),
    modules_json: str = Form("[]"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    template = NoteTemplate(user_id=user.id, is_builtin=False)
    _apply_form(db, user, template, name, description, category, icon, tags, title_pattern, modules_json)
    db.add(template)
    db.commit()
    return RedirectResponse("/notes/templates", status_code=303)


@router.post("/preview", response_class=HTMLResponse)
def preview_unsaved(
    name: str = Form("Voorbeeld"),
    modules_json: str = Form("[]"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """HTML-fragment voor de live-voorbeeldknop in de editor (niets wordt opgeslagen)."""
    template = NoteTemplate(user_id=user.id, name=name or "Voorbeeld")
    _apply_form(db, user, template, name or "Voorbeeld", "", "", "", "", "", modules_json)
    modules = db.query(NoteModule).filter(NoteModule.id.in_([m.module_id for m in template.modules])).all()
    by_id = {m.id: m for m in modules}
    for tm in template.modules:
        tm.module = by_id[tm.module_id]
    return HTMLResponse(_preview_html(template))


@router.get("/{template_id}/edit")
def edit_template_form(
    template_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    template = _get_template(db, template_id, user)
    if template.is_builtin:
        raise HTTPException(status_code=400, detail="Ingebouwde sjablonen zijn niet te bewerken; dupliceer ze eerst")
    return templates.TemplateResponse(request, "notes/templates_edit.html", _editor_context(user, db, template))


@router.post("/{template_id}/duplicate")
def duplicate_template(template_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    source = _get_template(db, template_id, user)
    copy = NoteTemplate(
        user_id=user.id,
        is_builtin=False,
        name=f"{source.name} (kopie)"[:120],
        description=source.description,
        category=source.category,
        icon=source.icon,
        tags=source.tags,
        title_pattern=source.title_pattern,
        modules=[
            NoteTemplateModule(
                module_id=tm.module_id, position=tm.position, title=tm.title, optional=tm.optional,
                default_content=tm.default_content, config=tm.config,
            )
            for tm in source.modules
        ],
    )
    db.add(copy)
    db.commit()
    return RedirectResponse(f"/notes/templates/{copy.id}/edit", status_code=303)


@router.post("/{template_id}/delete")
def delete_template(template_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    template = _get_template(db, template_id, user)
    if template.is_builtin:
        raise HTTPException(status_code=400, detail="Ingebouwde sjablonen kun je niet verwijderen (wel dupliceren)")
    db.delete(template)  # notities blijven bestaan: Note.template_id wordt NULL (ON DELETE SET NULL)
    db.commit()
    return RedirectResponse("/notes/templates", status_code=303)


@router.post("/{template_id}")
def update_template(
    template_id: int,
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    icon: str = Form("📝"),
    tags: str = Form(""),
    title_pattern: str = Form("{{title}}"),
    modules_json: str = Form("[]"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    template = _get_template(db, template_id, user)
    if template.is_builtin:
        raise HTTPException(status_code=400, detail="Ingebouwde sjablonen zijn niet te bewerken")
    _apply_form(db, user, template, name, description, category, icon, tags, title_pattern, modules_json)
    template.version += 1  # bestaande notities onthouden hun eigen (oude) versie
    db.commit()
    return RedirectResponse("/notes/templates", status_code=303)


# ---- Voorbeeld en gebruiken ----


@router.get("/{template_id}/preview")
def preview_template(
    template_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    template = _get_template(db, template_id, user)
    return templates.TemplateResponse(
        request, "notes/templates_preview.html", {"user": user, "template": template, "html": _preview_html(template)}
    )


@router.get("/{template_id}/use")
def use_template_form(
    template_id: int,
    request: Request,
    error: str = Query(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    template = _get_template(db, template_id, user)
    ctx = variable_context(template.name)
    default_title = resolve_vars(template.title_pattern, {**ctx, "title": template.name})
    return templates.TemplateResponse(
        request,
        "notes/templates_use.html",
        {
            "user": user,
            "template": template,
            "title": default_title,
            "modules": _form_modules(template, {**ctx, "title": default_title}),
            "tasks": _open_tasks(db, user),
            "error": error,
        },
    )


def _parse_use_form(form, modules: list[dict]) -> tuple[dict[int, dict], dict[int, list[dict]]]:
    values: dict[int, dict] = {}
    rows: dict[int, list[dict]] = {}
    grouped: dict[tuple[int, int], dict] = {}
    for key in form.keys():
        match = _ROW_KEY.match(key)
        if match:
            grouped.setdefault((int(match.group(1)), int(match.group(2))), {})[match.group(3)] = form.get(key)

    for module in modules:
        i = module["index"]
        if module["optional"] and not form.get(f"m{i}__include"):
            continue
        module_values = {}
        for field in module["fields"]:
            raw = form.get(f"m{i}__{field['name']}")
            module_values[field["name"]] = bool(raw) if field["type"] == "checkbox" else (raw or "")
        values[i] = module_values

        module_rows = []
        for (mi, _r), row in sorted(grouped.items()):
            if mi != i:
                continue
            for column in module["columns"]:
                if column["type"] == "checkbox":
                    row[column["name"]] = bool(row.get(column["name"]))
            has_content = any(
                str(v).strip() for k, v in row.items()
                if v and not isinstance(v, bool) and k != "status" and k not in ("likelihood", "impact")
            )
            if has_content:
                module_rows.append(row)
        rows[i] = module_rows
    return values, rows


@router.post("/{template_id}/use")
async def create_note_from_template(
    template_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    template = _get_template(db, template_id, user)
    form = await request.form()
    title = (form.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")

    ctx = variable_context(title)
    modules = _form_modules(template, ctx)
    values, rows = _parse_use_form(form, modules)

    missing = [
        f"{m['title'] or 'Veld'}: {f.get('label') or f['name']}"
        for m in modules if m["index"] in values
        for f in m["fields"]
        if f.get("required") and f["type"] != "checkbox" and not str(values[m["index"]].get(f["name"], "")).strip()
    ]
    if missing:
        raise HTTPException(status_code=400, detail="Verplichte velden ontbreken: " + ", ".join(missing))

    tag_names = ", ".join(x for x in (template.tags, form.get("tags") or "") if x.strip())
    tags = resolve_tags(db, tag_names)
    owned_tasks = {t.id: t for t in db.query(Task).filter(Task.user_id == user.id).all()}

    for module in modules:
        i = module["index"]
        if i not in rows:
            continue
        for row in rows[i]:
            # Bestaande taak gekozen: alleen koppelen (en alleen als 'ie echt van deze gebruiker is).
            try:
                linked = owned_tasks.get(int(row.get("task") or 0))
            except ValueError:
                linked = None
            row["task"] = str(linked.id) if linked else ""
            due = _parse_date(row.get("due"))

            if module["can_tasks"] and form.get(f"m{i}__create_tasks") and linked is None and row.get("text"):
                task = Task(user_id=user.id, title=str(row["text"])[:200], deadline=due)
                task.tags = list(tags)
                db.add(task)
                db.flush()
                owned_tasks[task.id] = task
                row["task"] = str(task.id)
            if module["can_events"] and form.get(f"m{i}__create_events") and due and row.get("text"):
                event = CalendarEvent(user_id=user.id, title=str(row["text"])[:200], event_date=due)
                event.tags = list(tags)
                db.add(event)

    note = Note(
        user_id=user.id,
        title=title,
        content=_render_note_html(modules, values, rows, owned_tasks),
        is_temp=bool(form.get("is_temp")),
        template_id=template.id,
        template_version=template.version,
        template_name=template.name,
    )
    note.tags = tags
    db.add(note)
    db.commit()
    return RedirectResponse(f"/notes/{note.id}/edit", status_code=303)


def _parse_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None
