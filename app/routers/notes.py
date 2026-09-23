from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.note import Note
from app.models.tag import Tag
from app.models.user import User
from app.services.richtext import sanitize_note_html
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/notes", tags=["notes"])

TEMP_NOTE_LIFETIME = timedelta(days=7)

_SORT_OPTIONS = {
    "updated": (Note.updated_at.desc(),),
    "title": (Note.title.asc(),),
    "created": (Note.created_at.desc(),),
}


def _delete_expired_temp_notes(db: Session, user_id: int) -> None:
    """Tijdelijke notities ("temp") ruimen zichzelf op zodra ze een week oud zijn.
    Er is bewust geen scheduler/cron in deze self-hosted app; in plaats daarvan
    wordt dit opportunistisch gedaan bij elk bezoek aan de notitielijst -- die
    pagina wordt vaak genoeg bezocht om verlopen notities snel te laten
    verdwijnen, zonder een extra achtergrondproces te hoeven draaien."""
    cutoff = datetime.now(UTC).replace(tzinfo=None) - TEMP_NOTE_LIFETIME
    db.query(Note).filter(Note.user_id == user_id, Note.is_temp.is_(True), Note.created_at < cutoff).delete(
        synchronize_session=False
    )
    db.commit()


def _get_note_or_404(db: Session, note_id: int, user_id: int) -> Note:
    note = (
        db.query(Note)
        .options(selectinload(Note.tags))
        .filter(Note.id == note_id, Note.user_id == user_id)
        .first()
    )
    if note is None:
        raise HTTPException(status_code=404, detail="Notitie niet gevonden")
    return note


@router.get("")
def list_notes(
    request: Request,
    tags: list[str] = Query(default=[]),
    sort: str = "updated",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _delete_expired_temp_notes(db, user.id)
    sort = sort if sort in _SORT_OPTIONS else "updated"
    query = db.query(Note).options(selectinload(Note.tags)).filter(Note.user_id == user.id)
    if tags:
        query = query.filter(Note.tags.any(Tag.name.in_(tags)))
    notes = query.order_by(*_SORT_OPTIONS[sort]).all()

    all_tags = (
        db.query(Tag)
        .join(Tag.notes)
        .filter(Note.user_id == user.id)
        .distinct()
        .order_by(Tag.name)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "notes/list.html",
        {"user": user, "notes": notes, "all_tags": all_tags, "active_tags": tags, "sort": sort},
    )


def _redirect_to_list(tag_filters: list[str], sort: str = "updated") -> RedirectResponse:
    params: dict[str, str | list[str]] = {"sort": sort}
    if tag_filters:
        params["tags"] = tag_filters
    return RedirectResponse(f"/notes?{urlencode(params, doseq=True)}", status_code=303)


@router.post("/bulk-delete")
async def bulk_delete_notes(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    form = await request.form()
    note_ids = [int(v) for v in form.getlist("note_ids")]
    if note_ids:
        db.query(Note).filter(Note.id.in_(note_ids), Note.user_id == user.id).delete(synchronize_session=False)
        db.commit()
    return _redirect_to_list(form.getlist("tag_filter"), form.get("sort", "updated"))


@router.post("/bulk-tag")
async def bulk_tag_notes(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Voegt een tag toe aan alle geselecteerde notities (bestaande tags blijven staan)."""
    form = await request.form()
    note_ids = [int(v) for v in form.getlist("note_ids")]
    tag_name = (form.get("tag") or "").strip()

    if note_ids and tag_name:
        notes = (
            db.query(Note)
            .options(selectinload(Note.tags))
            .filter(Note.id.in_(note_ids), Note.user_id == user.id)
            .all()
        )
        new_tags = resolve_tags(db, tag_name)
        for note in notes:
            for t in new_tags:
                if t not in note.tags:
                    note.tags.append(t)
        db.commit()
    return _redirect_to_list(form.getlist("tag_filter"), form.get("sort", "updated"))


@router.get("/new")
def new_note_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "notes/form.html", {"user": user, "note": None})


@router.post("")
def create_note(
    title: str = Form(...),
    content: str = Form(""),
    tags: str = Form(""),
    is_temp: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    note = Note(user_id=user.id, title=title.strip(), content=sanitize_note_html(content), is_temp=is_temp)
    note.tags = resolve_tags(db, tags)
    db.add(note)
    db.commit()
    return RedirectResponse("/notes", status_code=303)


@router.get("/{note_id}/edit")
def edit_note_form(
    note_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    note = _get_note_or_404(db, note_id, user.id)
    return templates.TemplateResponse(request, "notes/form.html", {"user": user, "note": note})


@router.post("/{note_id}")
def update_note(
    note_id: int,
    title: str = Form(...),
    content: str = Form(""),
    tags: str = Form(""),
    is_temp: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    note = _get_note_or_404(db, note_id, user.id)
    note.title = title.strip()
    note.content = sanitize_note_html(content)
    note.tags = resolve_tags(db, tags)
    note.is_temp = is_temp
    db.commit()
    return RedirectResponse("/notes", status_code=303)


@router.post("/{note_id}/delete")
def delete_note(note_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    note = _get_note_or_404(db, note_id, user.id)
    db.delete(note)
    db.commit()
    return RedirectResponse("/notes", status_code=303)
