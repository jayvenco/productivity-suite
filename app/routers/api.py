from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_api_user
from app.database import get_db
from app.models.kanban import KanbanBoard, KanbanCard, KanbanColumn, KanbanSwimlane
from app.models.note import Note
from app.models.snippet import Snippet, SnippetFile
from app.models.task import Task
from app.models.user import User
from app.services.richtext import sanitize_note_html
from app.services.kanban_cells import get_or_create_default_cell
from app.services.tags import resolve_tags

router = APIRouter(prefix="/api/v1", tags=["api"])


# ---- Taken ----


class TaskIn(BaseModel):
    title: str
    description: str = ""
    deadline: date | None = None
    tags: str = ""
    priority: bool = False


@router.post("/tasks")
def create_task_api(body: TaskIn, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")

    task = Task(user_id=user.id, title=title, description=body.description, deadline=body.deadline, priority=body.priority)
    task.tags = resolve_tags(db, body.tags)
    db.add(task)
    db.commit()
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "priority": task.priority,
        "tags": [t.name for t in task.tags],
        "url": f"/tasks/{task.id}/edit",
    }


# ---- Kanban-kaarten ----

_get_or_create_default_cell = get_or_create_default_cell


class KanbanCardIn(BaseModel):
    title: str
    description: str = ""
    tags: str = ""
    color: str | None = None
    swimlane_id: int | None = None
    column_id: int | None = None


@router.post("/kanban/cards")
def create_kanban_card_api(
    body: KanbanCardIn, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")

    board = db.query(KanbanBoard).filter(KanbanBoard.user_id == user.id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Geen kanbanbord gevonden")

    if body.swimlane_id is not None and body.column_id is not None:
        swimlane = db.get(KanbanSwimlane, body.swimlane_id)
        column = db.get(KanbanColumn, body.column_id)
        if swimlane is None or swimlane.board_id != board.id:
            raise HTTPException(status_code=404, detail="Swimlane niet gevonden")
        if column is None or column.swimlane_id != swimlane.id:
            raise HTTPException(status_code=404, detail="Kolom niet gevonden")
    else:
        swimlane, column = _get_or_create_default_cell(db, board)

    max_position = (
        db.query(KanbanCard)
        .filter(KanbanCard.column_id == column.id, KanbanCard.swimlane_id == swimlane.id)
        .count()
    )

    card = KanbanCard(
        board_id=board.id,
        column_id=column.id,
        swimlane_id=swimlane.id,
        title=title,
        description=body.description,
        color=body.color,
        position=max_position,
    )
    card.tags = resolve_tags(db, body.tags)
    db.add(card)
    db.commit()
    return {
        "id": card.id,
        "title": card.title,
        "description": card.description,
        "color": card.color,
        "swimlane_id": swimlane.id,
        "column_id": column.id,
        "tags": [t.name for t in card.tags],
        "url": "/kanban",
    }


# ---- Notities ----


class NoteIn(BaseModel):
    title: str
    content: str = ""
    tags: str = ""


@router.post("/notes")
def create_note_api(body: NoteIn, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")

    note = Note(user_id=user.id, title=title, content=sanitize_note_html(body.content))
    note.tags = resolve_tags(db, body.tags)
    db.add(note)
    db.commit()
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tags": [t.name for t in note.tags],
        "url": f"/notes/{note.id}/edit",
    }


# ---- Code snippets ----


class SnippetFileIn(BaseModel):
    filename: str
    language: str = "plaintext"
    content: str = ""


class SnippetIn(BaseModel):
    title: str
    tags: str = ""
    files: list[SnippetFileIn] = Field(min_length=1)


@router.post("/snippets")
def create_snippet_api(body: SnippetIn, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")

    snippet = Snippet(user_id=user.id, title=title)
    snippet.tags = resolve_tags(db, body.tags)
    db.add(snippet)
    db.flush()

    for position, file_in in enumerate(body.files):
        db.add(
            SnippetFile(
                snippet_id=snippet.id,
                filename=file_in.filename.strip() or f"bestand{position + 1}",
                language=(file_in.language or "plaintext").strip() or "plaintext",
                content=file_in.content,
                position=position,
            )
        )
    db.commit()
    return {
        "id": snippet.id,
        "title": snippet.title,
        "tags": [t.name for t in snippet.tags],
        "files": [{"filename": f.filename, "language": f.language} for f in snippet.files],
        "url": "/snippets",
    }
