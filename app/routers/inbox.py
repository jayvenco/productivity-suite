from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.inbox import InboxItem
from app.models.kanban import KanbanBoard
from app.models.user import User
from app.services import inbox as inbox_service
from app.templating import templates

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _get_item_or_404(db: Session, item_id: int, user_id: int) -> InboxItem:
    item = db.query(InboxItem).filter(InboxItem.id == item_id, InboxItem.user_id == user_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Inbox-item niet gevonden")
    return item


@router.get("")
def inbox_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    items = db.query(InboxItem).filter(InboxItem.user_id == user.id).order_by(InboxItem.created_at.desc(), InboxItem.id.desc()).all()
    board = (
        db.query(KanbanBoard)
        .options(selectinload(KanbanBoard.swimlanes))
        .filter(KanbanBoard.user_id == user.id)
        .first()
    )
    cells = []
    if board is not None:
        for swimlane in board.swimlanes:
            for column in swimlane.columns:
                cells.append({"value": f"{swimlane.id}:{column.id}", "label": f"{swimlane.name} · {column.name}"})
    return templates.TemplateResponse(request, "inbox/list.html", {"user": user, "items": items, "cells": cells})


@router.get("/count")
def inbox_count(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Aantal openstaande items, voor het label in het navigatiemenu."""
    return {"count": db.query(InboxItem).filter(InboxItem.user_id == user.id).count()}


@router.post("")
def add_item(
    request: Request,
    text: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Voegt een item toe. Vanuit het snelle invoervenster (fetch) komt er JSON terug, vanuit
    het formulier op de inbox-pagina een redirect."""
    clean = text.strip()
    if not clean:
        if request.headers.get("x-requested-with") == "fetch":
            return JSONResponse({"detail": "Tekst is leeg"}, status_code=400)
        return RedirectResponse("/inbox", status_code=303)
    item = InboxItem(user_id=user.id, text=clean)
    db.add(item)
    db.commit()
    if request.headers.get("x-requested-with") == "fetch":
        return {"id": item.id, "count": db.query(InboxItem).filter(InboxItem.user_id == user.id).count()}
    return RedirectResponse("/inbox", status_code=303)


@router.post("/{item_id}")
def update_item(
    item_id: int, text: str = Form(...), user: User = Depends(require_user), db: Session = Depends(get_db)
):
    item = _get_item_or_404(db, item_id, user.id)
    if text.strip():
        item.text = text.strip()
        db.commit()
    return RedirectResponse("/inbox", status_code=303)


@router.post("/{item_id}/delete")
def delete_item(item_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    db.delete(_get_item_or_404(db, item_id, user.id))
    db.commit()
    return RedirectResponse("/inbox", status_code=303)


@router.post("/{item_id}/to-note")
def item_to_note(
    item_id: int, tags: str = Form(""), user: User = Depends(require_user), db: Session = Depends(get_db)
):
    note = inbox_service.to_note(db, user, _get_item_or_404(db, item_id, user.id), tags)
    return RedirectResponse(f"/notes/{note.id}/edit", status_code=303)


@router.post("/{item_id}/to-task")
def item_to_task(
    item_id: int,
    deadline: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        parsed = date.fromisoformat(deadline) if deadline else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ongeldige deadline") from exc
    task = inbox_service.to_task(db, user, _get_item_or_404(db, item_id, user.id), parsed, tags)
    return RedirectResponse(f"/tasks/{task.id}/edit", status_code=303)


@router.post("/{item_id}/to-card")
def item_to_card(
    item_id: int,
    cell: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    swimlane_id = column_id = None
    if cell:
        try:
            swimlane_id, column_id = (int(part) for part in cell.split(":"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Ongeldige kolom") from exc
    inbox_service.to_card(db, user, _get_item_or_404(db, item_id, user.id), swimlane_id, column_id, tags)
    return RedirectResponse("/kanban", status_code=303)
