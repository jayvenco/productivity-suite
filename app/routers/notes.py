from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.note import Note
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import render_markdown, templates

router = APIRouter(prefix="/notes", tags=["notes"])


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
    tag: str | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(Note).options(selectinload(Note.tags)).filter(Note.user_id == user.id)
    if tag:
        query = query.filter(Note.tags.any(name=tag))
    notes = query.order_by(Note.updated_at.desc()).all()

    return templates.TemplateResponse(
        request, "notes/list.html", {"user": user, "notes": notes, "active_tag": tag}
    )


@router.post("/preview")
def preview_note(content: str = Form(""), user: User = Depends(require_user)):
    """Rendert markdown server-side voor de live preview in het notitie-formulier --
    zo hoeft er geen aparte markdown-parser in JS meegeleverd te worden."""
    return HTMLResponse(render_markdown(content))


@router.get("/new")
def new_note_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "notes/form.html", {"user": user, "note": None})


@router.post("")
def create_note(
    title: str = Form(...),
    content: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    note = Note(user_id=user.id, title=title.strip(), content=content)
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    note = _get_note_or_404(db, note_id, user.id)
    note.title = title.strip()
    note.content = content
    note.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/notes", status_code=303)


@router.post("/{note_id}/delete")
def delete_note(note_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    note = _get_note_or_404(db, note_id, user.id)
    db.delete(note)
    db.commit()
    return RedirectResponse("/notes", status_code=303)
