"""Inbox-items omzetten naar een notitie, taak of kanban-kaart. Eén plek, gedeeld door de
webinterface en de JSON-API (en daarmee de MCP-server)."""

from __future__ import annotations

import html
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.inbox import InboxItem
from app.models.kanban import KanbanBoard, KanbanCard, KanbanColumn, KanbanSwimlane
from app.models.note import Note
from app.models.task import Task
from app.models.user import User
from app.services.kanban_cells import get_or_create_default_cell
from app.services.richtext import looks_like_html, sanitize_note_html, sanitize_rich, split_rich
from app.services.tags import resolve_tags

TITLE_MAX = 200


def split_text(text: str) -> tuple[str, str]:
    """Eerste regel/blok = titel (max. 200 tekens), de rest = beschrijving (HTML of platte tekst)."""
    return split_rich(text)


def to_note(db: Session, user: User, item: InboxItem, tags: str = "") -> Note:
    title, rest = split_text(item.text)
    if looks_like_html(rest):
        content = sanitize_note_html(rest)
    else:
        content = sanitize_note_html("".join(f"<p>{html.escape(line)}</p>" for line in rest.splitlines() if line.strip()))
    note = Note(user_id=user.id, title=title or "Inbox-notitie", content=content)
    note.tags = resolve_tags(db, tags)
    db.add(note)
    db.delete(item)
    db.commit()
    return note


def to_task(db: Session, user: User, item: InboxItem, deadline: date | None = None, tags: str = "") -> Task:
    title, rest = split_text(item.text)
    task = Task(user_id=user.id, title=title or "Inbox-taak", description=sanitize_rich(rest), deadline=deadline)
    task.tags = resolve_tags(db, tags)
    db.add(task)
    db.delete(item)
    db.commit()
    return task


def to_card(
    db: Session,
    user: User,
    item: InboxItem,
    swimlane_id: int | None = None,
    column_id: int | None = None,
    tags: str = "",
) -> KanbanCard:
    board = db.query(KanbanBoard).filter(KanbanBoard.user_id == user.id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Geen kanbanbord gevonden")

    if swimlane_id is not None and column_id is not None:
        swimlane = db.get(KanbanSwimlane, swimlane_id)
        column = db.get(KanbanColumn, column_id)
        if swimlane is None or swimlane.board_id != board.id:
            raise HTTPException(status_code=404, detail="Swimlane niet gevonden")
        if column is None or column.swimlane_id != swimlane.id:
            raise HTTPException(status_code=404, detail="Kolom niet gevonden")
    else:
        swimlane, column = get_or_create_default_cell(db, board)

    position = (
        db.query(KanbanCard)
        .filter(KanbanCard.column_id == column.id, KanbanCard.swimlane_id == swimlane.id)
        .count()
    )
    title, rest = split_text(item.text)
    card = KanbanCard(
        board_id=board.id,
        column_id=column.id,
        swimlane_id=swimlane.id,
        title=title or "Inbox-kaart",
        description=sanitize_rich(rest),
        position=position,
    )
    card.tags = resolve_tags(db, tags)
    db.add(card)
    db.delete(item)
    db.commit()
    return card
