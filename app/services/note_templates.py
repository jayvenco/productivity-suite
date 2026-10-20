"""Sjabloonsysteem voor notities: moduletypen (register), variabelen, HTML-rendering en seeding.

Alles is gegevensgedreven: een sjabloon is een geordende lijst modules, elke module heeft een
`type` uit MODULE_TYPES en wordt door één generieke renderer/formulier-macro afgehandeld.
Een nieuw sjabloon of een nieuwe combinatie van modules vraagt dus geen nieuwe code."""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

import markdown as md
from sqlalchemy.orm import Session

from app.models.note_template import NoteModule, NoteTemplate, NoteTemplateModule
from app.services.note_template_data import TEMPLATES

FIELD_TYPES = ["text", "textarea", "number", "date", "checkbox", "select", "url", "task"]
STATUS_OPTIONS = ["Te doen", "Bezig", "Klaar"]
LEVEL_OPTIONS = ["Laag", "Midden", "Hoog"]


def F(name: str, type: str = "text", label: str | None = None, **kw: Any) -> dict:
    return {"name": name, "type": type, "label": label or name.capitalize(), **kw}


# kind: "fields" (veldenlijst uit config), "single" (vaste velden), "list" (herhaalbare rijen met
# kolommen). can_tasks/can_events: rijen mogen als taak / kalenderafspraak worden aangemaakt.
MODULE_TYPES: dict[str, dict] = {
    "fields": {"label": "Velden (gestructureerd)", "kind": "fields", "fields": []},
    "text": {"label": "Vrije tekst", "kind": "single", "fields": [F("text", "textarea", "Tekst")]},
    "richtext": {
        "label": "Markdown-sectie",
        "kind": "single",
        "fields": [F("text", "textarea", "Markdown", placeholder="**vet**, - lijsten, [links](https://...)")],
    },
    "heading": {
        "label": "Kop en beschrijving",
        "kind": "single",
        "fields": [F("text", "textarea", "Beschrijving")],
    },
    "checklist": {
        "label": "Checklist",
        "kind": "list",
        "columns": [F("text", "text", "Item"), F("done", "checkbox", "Klaar")],
    },
    "action_items": {
        "label": "Actiepunten",
        "kind": "list",
        "can_tasks": True,
        "columns": [
            F("text", "text", "Actie"),
            F("owner", "text", "Eigenaar"),
            F("due", "date", "Deadline"),
            F("task", "task", "Bestaande taak"),
        ],
    },
    "agenda": {
        "label": "Agendapunten",
        "kind": "list",
        "columns": [F("text", "text", "Onderwerp"), F("minutes", "number", "Minuten"), F("task", "task", "Taak")],
    },
    "decisions": {
        "label": "Besluiten",
        "kind": "list",
        "columns": [F("text", "text", "Besluit"), F("rationale", "text", "Onderbouwing"), F("owner", "text", "Eigenaar")],
    },
    "milestones": {
        "label": "Mijlpalen",
        "kind": "list",
        "can_events": True,
        "columns": [F("text", "text", "Mijlpaal"), F("due", "date", "Datum"), F("done", "checkbox", "Klaar")],
    },
    "steps": {
        "label": "Stappenlijst",
        "kind": "list",
        "can_tasks": True,
        "columns": [
            F("text", "text", "Stap"),
            F("owner", "text", "Eigenaar"),
            F("due", "date", "Deadline"),
            F("status", "select", "Status", options=STATUS_OPTIONS),
            F("task", "task", "Bestaande taak"),
        ],
    },
    "roles": {
        "label": "Rollen en verantwoordelijkheden",
        "kind": "list",
        "columns": [
            F("text", "text", "Rol"),
            F("person", "text", "Persoon/team"),
            F("responsibilities", "text", "Verantwoordelijkheden"),
            F("authority", "text", "Besluitbevoegdheid"),
            F("escalation", "text", "Escalatiecontact"),
        ],
    },
    "risks": {
        "label": "Risicoregister",
        "kind": "list",
        "columns": [
            F("text", "text", "Risico"),
            F("likelihood", "select", "Kans", options=LEVEL_OPTIONS),
            F("impact", "select", "Impact", options=LEVEL_OPTIONS),
            F("mitigation", "text", "Maatregel"),
            F("owner", "text", "Eigenaar"),
        ],
    },
    "pros_cons": {
        "label": "Voor- en nadelen",
        "kind": "single",
        "fields": [F("pros", "textarea", "Voordelen", placeholder="één per regel"),
                   F("cons", "textarea", "Nadelen", placeholder="één per regel")],
    },
    "links": {
        "label": "Links en referenties",
        "kind": "list",
        "columns": [F("text", "text", "Omschrijving"), F("url", "url", "URL")],
    },
    "questions": {
        "label": "Vragen en open punten",
        "kind": "list",
        "columns": [F("text", "text", "Vraag"), F("owner", "text", "Wie zoekt het uit")],
    },
    "notes": {
        "label": "Notities en observaties",
        "kind": "single",
        "fields": [F("text", "textarea", "Notities")],
    },
}


# ---- Variabelen ----

_VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def variable_context(title: str = "", now: datetime | None = None) -> dict[str, str]:
    now = now or datetime.now()
    return {
        "title": title,
        "date": now.date().isoformat(),
        "datetime": now.strftime("%Y-%m-%d %H:%M"),
        "week": str(now.isocalendar().week),
    }


def resolve_vars(text: str, ctx: dict[str, str]) -> str:
    """Vervangt {{title}}, {{date}}, {{datetime}} en {{week}}; onbekende variabelen blijven staan."""
    return _VAR.sub(lambda m: ctx.get(m.group(1), m.group(0)), text or "")


# ---- Veld- en rijdefinities per sjabloonmodule ----


def module_fields(mtype: str, config: dict) -> list[dict]:
    spec = MODULE_TYPES.get(mtype, MODULE_TYPES["text"])
    if spec["kind"] == "fields":
        return [f for f in config.get("fields", []) if isinstance(f, dict) and f.get("name")]
    if spec["kind"] == "single":
        return spec["fields"]
    return []


def module_columns(mtype: str) -> list[dict]:
    return MODULE_TYPES.get(mtype, {}).get("columns", [])


# ---- Rendering naar notitie-HTML ----

_esc = html.escape


def _multiline(value: str) -> str:
    return "<br>".join(_esc(line) for line in value.splitlines())


def _task_link(task_id: str, tasks: dict[int, Any]) -> str:
    try:
        task = tasks.get(int(task_id))
    except (TypeError, ValueError):
        task = None
    return f'<a href="/tasks/{task.id}/edit">{_esc(task.title)}</a>' if task else ""


def _format_value(field: dict, value: Any, tasks: dict[int, Any]) -> str:
    ftype = field.get("type", "text")
    if ftype == "checkbox":
        return "☑" if value else "☐"
    value = "" if value is None else str(value)
    if not value.strip():
        return ""
    if ftype == "textarea":
        return _multiline(value)
    if ftype == "url":
        return f'<a href="{_esc(value, quote=True)}">{_esc(value)}</a>'
    if ftype == "task":
        return _task_link(value, tasks)
    return _esc(value)


def _li(parts: list[str]) -> str:
    return "<li>" + " ".join(p for p in parts if p) + "</li>"


def _row_html(mtype: str, row: dict, tasks: dict[int, Any]) -> str:
    g = lambda k: _esc(str(row.get(k) or ""))  # noqa: E731
    text = g("text")
    link = _task_link(row.get("task", ""), tasks)
    try:
        linked = tasks.get(int(row.get("task") or 0))
    except (TypeError, ValueError):
        linked = None
    if linked is not None and (not text or html.unescape(text) == linked.title):
        text = ""  # de link toont al dezelfde titel; niet dubbel tonen
    if mtype == "checklist":
        return _li([("☑" if row.get("done") else "☐"), text])
    if mtype == "action_items":
        extra = [f"— {g('owner')}" if row.get("owner") else "", f"(deadline {g('due')})" if row.get("due") else ""]
        return _li(["☑" if row.get("done") else "☐", text, *extra, link])
    if mtype == "agenda":
        return _li([text, f"({g('minutes')} min)" if row.get("minutes") else "", link])
    if mtype == "decisions":
        return _li([f"<strong>{text}</strong>", f"— {g('rationale')}" if row.get("rationale") else "",
                    f"({g('owner')})" if row.get("owner") else ""])
    if mtype == "milestones":
        return _li([("☑" if row.get("done") else "☐"), g("due"), "—" if row.get("due") else "", text])
    if mtype == "steps":
        meta = [m for m in (g("owner"), f"deadline {g('due')}" if row.get("due") else "", g("status")) if m]
        return _li([text, f"· {' · '.join(meta)}" if meta else "", link])
    if mtype == "roles":
        bits = [(g(k), lbl) for k, lbl in (("responsibilities", "verantwoordelijk voor"), ("authority", "bevoegdheid"),
                                           ("escalation", "escalatie")) if row.get(k)]
        return _li([f"<strong>{text}</strong>", f"— {g('person')}" if row.get("person") else "",
                    "; ".join(f"{lbl}: {val}" for val, lbl in bits)])
    if mtype == "risks":
        return _li([f"<strong>{text}</strong>",
                    f"(kans {g('likelihood')}, impact {g('impact')})" if row.get("likelihood") or row.get("impact") else "",
                    f"— {g('mitigation')}" if row.get("mitigation") else "", f"[{g('owner')}]" if row.get("owner") else ""])
    if mtype == "links":
        url = row.get("url") or ""
        return _li([f'<a href="{_esc(url, quote=True)}">{text or _esc(url)}</a>' if url else text])
    if mtype == "questions":
        return _li([text, f"({g('owner')})" if row.get("owner") else ""])
    return _li([text])


def render_module(
    mtype: str, title: str, config: dict, values: dict, rows: list[dict], tasks: dict[int, Any], default: str = ""
) -> str:
    """Geeft de HTML voor één module (wordt daarna als geheel door sanitize_note_html gehaald)."""
    spec = MODULE_TYPES.get(mtype, MODULE_TYPES["text"])
    out = [f"<h2>{_esc(title)}</h2>"] if title else []

    if spec["kind"] == "fields":
        for field in module_fields(mtype, config):
            out.append(f"<p><strong>{_esc(field.get('label') or field['name'])}:</strong> "
                       f"{_format_value(field, values.get(field['name']), tasks)}</p>")
    elif spec["kind"] == "list":
        tag = "ol" if mtype in ("agenda", "steps") else "ul"
        items = [_row_html(mtype, row, tasks) for row in rows] or ["<li></li>"]
        out.append(f"<{tag}>{''.join(items)}</{tag}>")
    elif mtype == "pros_cons":
        for field in spec["fields"]:
            lines = [ln.strip() for ln in str(values.get(field["name"]) or "").splitlines() if ln.strip()]
            out.append(f"<p><strong>{_esc(field['label'])}</strong></p>"
                       f"<ul>{''.join(f'<li>{_esc(ln)}</li>' for ln in lines) or '<li></li>'}</ul>")
    else:  # single text/markdown/notes/heading
        text = str(values.get("text") or "")
        if mtype == "richtext" and text.strip():
            out.append(md.markdown(text))
        elif text.strip():
            out.append("".join(f"<p>{_esc(line)}</p>" for line in text.splitlines() if line.strip()))
        else:
            out.append("<p></p>")

    if default.strip():
        out.append("".join(f"<p><em>{_esc(line)}</em></p>" for line in default.splitlines() if line.strip()))
    return "".join(out)


# ---- Seeding van modulebibliotheek en ingebouwde sjablonen ----


def _ensure_builtin_modules(db: Session) -> dict[str, NoteModule]:
    existing = {m.key: m for m in db.query(NoteModule).filter(NoteModule.is_builtin.is_(True)).all()}
    for key, spec in MODULE_TYPES.items():
        if key not in existing:
            module = NoteModule(key=key, name=spec["label"], type=key, is_builtin=True)
            db.add(module)
            existing[key] = module
    db.flush()
    return existing


def _apply_definition(db: Session, template: NoteTemplate, definition: dict, modules: dict[str, NoteModule]) -> None:
    import json

    template.name = definition["name"]
    template.description = definition.get("description", "")
    template.category = definition["category"]
    template.icon = definition.get("icon", "📝")
    template.tags = definition.get("tags", "")
    template.title_pattern = definition.get("title_pattern", "{{title}}")
    template.modules = [
        NoteTemplateModule(
            module_id=modules[spec["type"]].id,
            position=position,
            title=spec.get("title", ""),
            optional=spec.get("optional", False),
            default_content=spec.get("default", ""),
            config=json.dumps(spec["config"], ensure_ascii=False) if spec.get("config") else "",
        )
        for position, spec in enumerate(definition["modules"])
    ]


def seed_builtin_templates(db: Session, reset: bool = False) -> int:
    """Maakt ontbrekende ingebouwde sjablonen aan (bij elke start). Met reset=True worden ze
    ook terug naar hun oorspronkelijke definitie gezet ("Standaardsjablonen herstellen") --
    bestaande notities blijven onaangetast, die zijn zelfstandig. Geeft het aantal
    aangemaakte/herstelde sjablonen terug."""
    modules = _ensure_builtin_modules(db)
    existing = {t.builtin_key: t for t in db.query(NoteTemplate).filter(NoteTemplate.is_builtin.is_(True)).all()}
    changed = 0
    for definition in TEMPLATES:
        template = existing.get(definition["key"])
        if template is None:
            template = NoteTemplate(builtin_key=definition["key"], is_builtin=True)
            db.add(template)
        elif not reset:
            continue
        else:
            template.version += 1
        _apply_definition(db, template, definition, modules)
        changed += 1
    db.commit()
    return changed


