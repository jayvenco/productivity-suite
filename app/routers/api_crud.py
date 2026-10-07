"""List/get/update/delete-routes onder /api/v1 (de create-routes staan in api.py).

Dunne JSON-laag bovenop dezelfde modellen en services als de form-routes: tags gaan als
komma-gescheiden string erin en als lijst eruit, lijsten hebben limit/offset + total.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_api_user
from app.database import get_db
from app.models.kanban import KanbanBoard, KanbanCard, KanbanColumn, KanbanSwimlane
from app.models.note import Note
from app.models.snippet import Snippet, SnippetFile
from app.models.tag import Tag
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.routers.api import router
from app.routers.notes import TEMP_NOTE_LIFETIME
from app.routers.tasks import _apply_status, _archive_and_purge_tasks
from app.services.checklist import checklist_progress, toggle_checklist_line
from app.services.richtext import sanitize_note_html
from app.services.tags import resolve_tags

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

Tags = str | list[str]


def _tags_in(raw: Tags) -> str:
    return ", ".join(raw) if isinstance(raw, list) else raw


def _page(query, limit: int, offset: int, serialize) -> dict:
    total = query.count()
    items = query.limit(limit).offset(offset).all()
    return {"items": [serialize(i) for i in items], "total": total, "limit": limit, "offset": offset}


def _deleted(item_id: int) -> dict:
    return {"deleted": True, "id": item_id}


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value else None


# ---- Taken ----


def task_out(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "deadline": _iso(task.deadline),
        "priority": task.priority,
        "daily_task": task.daily_task,
        "status": task.status.value,
        "done": task.status == TaskStatus.DONE,
        "archived": task.archived_at is not None,
        "tags": [t.name for t in task.tags],
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
        "completed_at": _iso(task.completed_at),
        "url": f"/tasks/{task.id}/edit",
    }


def _get_task(db: Session, task_id: int, user: User) -> Task:
    task = (
        db.query(Task)
        .options(selectinload(Task.tags))
        .filter(Task.id == task_id, Task.user_id == user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Taak niet gevonden")
    return task


@router.get("/tasks")
def list_tasks_api(
    status: str | None = Query(None, pattern="^(open|done|archived)$"),
    tag: str | None = None,
    priority: bool | None = None,
    due_before: date | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    _archive_and_purge_tasks(db, user.id)
    query = db.query(Task).options(selectinload(Task.tags)).filter(Task.user_id == user.id)
    if status == "archived":
        query = query.filter(Task.archived_at.isnot(None))
    else:
        query = query.filter(Task.archived_at.is_(None))
        if status == "open":
            query = query.filter(Task.status != TaskStatus.DONE)
        elif status == "done":
            query = query.filter(Task.status == TaskStatus.DONE)
    if tag:
        query = query.filter(Task.tags.any(Tag.name == tag))
    if priority is not None:
        query = query.filter(Task.priority.is_(priority))
    if due_before:
        query = query.filter(Task.deadline.isnot(None), Task.deadline < due_before)
    return _page(query.order_by(Task.created_at.desc(), Task.id.desc()), limit, offset, task_out)


@router.get("/tasks/{task_id}")
def get_task_api(task_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    return task_out(_get_task(db, task_id, user))


class TaskPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    deadline: date | None = None
    tags: Tags | None = None
    priority: bool | None = None
    daily_task: bool | None = None
    done: bool | None = None


@router.patch("/tasks/{task_id}")
def patch_task_api(
    task_id: int, body: TaskPatch, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    task = _get_task(db, task_id, user)
    sent = body.model_fields_set
    if "title" in sent:
        title = (body.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Titel is verplicht")
        task.title = title
    if "description" in sent and body.description is not None:
        task.description = body.description
    if "deadline" in sent:
        task.deadline = body.deadline
    if "tags" in sent and body.tags is not None:
        task.tags = resolve_tags(db, _tags_in(body.tags))
    if "priority" in sent and body.priority is not None:
        task.priority = body.priority
    if "daily_task" in sent and body.daily_task is not None:
        task.daily_task = body.daily_task
    if "done" in sent and body.done is not None:
        _apply_status(task, TaskStatus.DONE if body.done else TaskStatus.TODO)
    db.commit()
    return task_out(task)


@router.delete("/tasks/{task_id}")
def delete_task_api(task_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    db.delete(_get_task(db, task_id, user))
    db.commit()
    return _deleted(task_id)


@router.post("/tasks/{task_id}/toggle-done")
def toggle_task_done_api(task_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    task = _get_task(db, task_id, user)
    _apply_status(task, TaskStatus.TODO if task.status == TaskStatus.DONE else TaskStatus.DONE)
    db.commit()
    return task_out(task)


@router.post("/tasks/{task_id}/restore")
def restore_task_api(task_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    task = _get_task(db, task_id, user)
    _apply_status(task, TaskStatus.TODO)
    db.commit()
    return task_out(task)


# ---- Notities ----


def note_out(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "is_temp": note.is_temp,
        "tags": [t.name for t in note.tags],
        "created_at": _iso(note.created_at),
        "updated_at": _iso(note.updated_at),
        "url": f"/notes/{note.id}/edit",
    }


def _get_note(db: Session, note_id: int, user: User) -> Note:
    note = (
        db.query(Note)
        .options(selectinload(Note.tags))
        .filter(Note.id == note_id, Note.user_id == user.id)
        .first()
    )
    if note is None:
        raise HTTPException(status_code=404, detail="Notitie niet gevonden")
    return note


@router.get("/notes")
def list_notes_api(
    tag: str | None = None,
    is_temp: bool | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(UTC).replace(tzinfo=None) - TEMP_NOTE_LIFETIME
    db.query(Note).filter(Note.user_id == user.id, Note.is_temp.is_(True), Note.created_at < cutoff).delete(
        synchronize_session=False
    )
    db.commit()
    query = db.query(Note).options(selectinload(Note.tags)).filter(Note.user_id == user.id)
    if tag:
        query = query.filter(Note.tags.any(Tag.name == tag))
    if is_temp is not None:
        query = query.filter(Note.is_temp.is_(is_temp))
    return _page(query.order_by(Note.created_at.desc(), Note.id.desc()), limit, offset, note_out)


@router.get("/notes/{note_id}")
def get_note_api(note_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    return note_out(_get_note(db, note_id, user))


class NotePatch(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: Tags | None = None
    is_temp: bool | None = None


@router.patch("/notes/{note_id}")
def patch_note_api(
    note_id: int, body: NotePatch, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    note = _get_note(db, note_id, user)
    sent = body.model_fields_set
    if "title" in sent:
        title = (body.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Titel is verplicht")
        note.title = title
    if "content" in sent and body.content is not None:
        note.content = sanitize_note_html(body.content)
    if "tags" in sent and body.tags is not None:
        note.tags = resolve_tags(db, _tags_in(body.tags))
    if "is_temp" in sent and body.is_temp is not None:
        note.is_temp = body.is_temp
    db.commit()
    return note_out(note)


@router.delete("/notes/{note_id}")
def delete_note_api(note_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    db.delete(_get_note(db, note_id, user))
    db.commit()
    return _deleted(note_id)


# ---- Snippets ----


def snippet_out(snippet: Snippet) -> dict:
    return {
        "id": snippet.id,
        "title": snippet.title,
        "description": snippet.description,
        "tags": [t.name for t in snippet.tags],
        "files": [
            {"id": f.id, "filename": f.filename, "language": f.language, "content": f.content}
            for f in snippet.files
        ],
        "created_at": _iso(snippet.created_at),
        "updated_at": _iso(snippet.updated_at),
        "url": "/snippets",
    }


def _get_snippet(db: Session, snippet_id: int, user: User) -> Snippet:
    snippet = (
        db.query(Snippet)
        .options(selectinload(Snippet.tags), selectinload(Snippet.files))
        .filter(Snippet.id == snippet_id, Snippet.user_id == user.id)
        .first()
    )
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet niet gevonden")
    return snippet


@router.get("/snippets")
def list_snippets_api(
    tag: str | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Snippet)
        .options(selectinload(Snippet.tags), selectinload(Snippet.files))
        .filter(Snippet.user_id == user.id)
    )
    if tag:
        query = query.filter(Snippet.tags.any(Tag.name == tag))
    return _page(query.order_by(Snippet.created_at.desc(), Snippet.id.desc()), limit, offset, snippet_out)


@router.get("/snippets/{snippet_id}")
def get_snippet_api(snippet_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    return snippet_out(_get_snippet(db, snippet_id, user))


class SnippetFilePatch(BaseModel):
    filename: str
    language: str = "plaintext"
    content: str = ""


class SnippetPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: Tags | None = None
    files: list[SnippetFilePatch] | None = None  # optioneel: vervangt alle bestanden


@router.patch("/snippets/{snippet_id}")
def patch_snippet_api(
    snippet_id: int, body: SnippetPatch, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    snippet = _get_snippet(db, snippet_id, user)
    sent = body.model_fields_set
    if "title" in sent:
        title = (body.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Titel is verplicht")
        snippet.title = title
    if "description" in sent and body.description is not None:
        snippet.description = body.description
    if "tags" in sent and body.tags is not None:
        snippet.tags = resolve_tags(db, _tags_in(body.tags))
    if "files" in sent and body.files is not None:
        if not body.files:
            raise HTTPException(status_code=400, detail="Een snippet heeft minstens één bestand nodig")
        snippet.files = [
            SnippetFile(
                filename=f.filename.strip() or f"bestand{i + 1}",
                language=(f.language or "plaintext").strip() or "plaintext",
                content=f.content,
                position=i,
            )
            for i, f in enumerate(body.files)
        ]
    db.commit()
    return snippet_out(snippet)


@router.delete("/snippets/{snippet_id}")
def delete_snippet_api(snippet_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    db.delete(_get_snippet(db, snippet_id, user))
    db.commit()
    return _deleted(snippet_id)


# ---- Kanban ----


def _board(db: Session, user: User) -> KanbanBoard:
    board = (
        db.query(KanbanBoard)
        .options(selectinload(KanbanBoard.swimlanes).selectinload(KanbanSwimlane.columns))
        .filter(KanbanBoard.user_id == user.id)
        .first()
    )
    if board is None:
        raise HTTPException(status_code=404, detail="Geen kanbanbord gevonden")
    return board


def card_out(card: KanbanCard) -> dict:
    done, total = checklist_progress(card.description or "")
    return {
        "id": card.id,
        "title": card.title,
        "description": card.description,
        "color": card.color,
        "swimlane_id": card.swimlane_id,
        "column_id": card.column_id,
        "position": card.position,
        "task_id": card.task_id,
        "tags": [t.name for t in card.tags],
        "checklist": {"done": done, "total": total},
        "created_at": _iso(card.created_at),
        "url": "/kanban",
    }


def swimlane_out(swimlane: KanbanSwimlane) -> dict:
    return {
        "id": swimlane.id,
        "name": swimlane.name,
        "color": swimlane.color,
        "position": swimlane.position,
        "columns": [{"id": c.id, "name": c.name, "position": c.position} for c in swimlane.columns],
        "url": "/kanban",
    }


def _get_card(db: Session, card_id: int, board: KanbanBoard) -> KanbanCard:
    card = (
        db.query(KanbanCard)
        .options(selectinload(KanbanCard.tags))
        .filter(KanbanCard.id == card_id, KanbanCard.board_id == board.id)
        .first()
    )
    if card is None:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")
    return card


def _get_swimlane(db: Session, swimlane_id: int, board: KanbanBoard) -> KanbanSwimlane:
    swimlane = db.get(KanbanSwimlane, swimlane_id)
    if swimlane is None or swimlane.board_id != board.id:
        raise HTTPException(status_code=404, detail="Swimlane niet gevonden")
    return swimlane


@router.get("/kanban")
def get_board_api(user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    board = _board(db, user)
    cards = (
        db.query(KanbanCard)
        .options(selectinload(KanbanCard.tags))
        .filter(KanbanCard.board_id == board.id)
        .order_by(KanbanCard.position, KanbanCard.id)
        .all()
    )
    by_column: dict[int, list[KanbanCard]] = {}
    for card in cards:
        by_column.setdefault(card.column_id, []).append(card)
    return {
        "id": board.id,
        "name": board.name,
        "swimlanes": [
            {
                "id": s.id,
                "name": s.name,
                "color": s.color,
                "position": s.position,
                "columns": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "position": c.position,
                        "cards": [card_out(card) for card in by_column.get(c.id, []) if card.swimlane_id == s.id],
                    }
                    for c in s.columns
                ],
            }
            for s in board.swimlanes
        ],
    }


@router.get("/kanban/cards")
def list_cards_api(
    swimlane_id: int | None = None,
    column_id: int | None = None,
    tag: str | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    board = _board(db, user)
    query = db.query(KanbanCard).options(selectinload(KanbanCard.tags)).filter(KanbanCard.board_id == board.id)
    if swimlane_id is not None:
        query = query.filter(KanbanCard.swimlane_id == swimlane_id)
    if column_id is not None:
        query = query.filter(KanbanCard.column_id == column_id)
    if tag:
        query = query.filter(KanbanCard.tags.any(Tag.name == tag))
    return _page(query.order_by(KanbanCard.created_at.desc(), KanbanCard.id.desc()), limit, offset, card_out)


@router.get("/kanban/cards/{card_id}")
def get_card_api(card_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    return card_out(_get_card(db, card_id, _board(db, user)))


class CardPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: Tags | None = None
    color: str | None = None  # expliciet null/"" wist de kleur


@router.patch("/kanban/cards/{card_id}")
def patch_card_api(
    card_id: int, body: CardPatch, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    card = _get_card(db, card_id, _board(db, user))
    sent = body.model_fields_set
    if "title" in sent:
        title = (body.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Titel is verplicht")
        card.title = title
    if "description" in sent and body.description is not None:
        card.description = body.description
    if "tags" in sent and body.tags is not None:
        card.tags = resolve_tags(db, _tags_in(body.tags))
    if "color" in sent:
        card.color = body.color or None
    db.commit()
    return card_out(card)


@router.delete("/kanban/cards/{card_id}")
def delete_card_api(card_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    db.delete(_get_card(db, card_id, _board(db, user)))
    db.commit()
    return _deleted(card_id)


class CardMove(BaseModel):
    swimlane_id: int
    column_id: int
    position: int = 0


@router.post("/kanban/cards/{card_id}/move")
def move_card_api(
    card_id: int, body: CardMove, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    board = _board(db, user)
    card = _get_card(db, card_id, board)
    swimlane = _get_swimlane(db, body.swimlane_id, board)
    column = db.get(KanbanColumn, body.column_id)
    if column is None or column.swimlane_id != swimlane.id:
        raise HTTPException(status_code=404, detail="Kolom niet gevonden")
    card.swimlane_id = swimlane.id
    card.column_id = column.id
    card.position = body.position
    db.commit()
    return card_out(card)


class ChecklistToggle(BaseModel):
    line_index: int


@router.post("/kanban/cards/{card_id}/checklist-toggle")
def toggle_card_checklist_api(
    card_id: int, body: ChecklistToggle, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    card = _get_card(db, card_id, _board(db, user))
    card.description = toggle_checklist_line(card.description, body.line_index)
    db.commit()
    return card_out(card)


@router.get("/kanban/swimlanes")
def list_swimlanes_api(user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    board = _board(db, user)
    return {"items": [swimlane_out(s) for s in board.swimlanes], "total": len(board.swimlanes)}


class SwimlanePatch(BaseModel):
    name: str | None = None
    color: str | None = None


@router.patch("/kanban/swimlanes/{swimlane_id}")
def patch_swimlane_api(
    swimlane_id: int, body: SwimlanePatch, user: User = Depends(require_api_user), db: Session = Depends(get_db)
):
    swimlane = _get_swimlane(db, swimlane_id, _board(db, user))
    sent = body.model_fields_set
    if "name" in sent:
        name = (body.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Naam is verplicht")
        swimlane.name = name
    if "color" in sent:
        swimlane.color = body.color or None
    db.commit()
    return swimlane_out(swimlane)


@router.delete("/kanban/swimlanes/{swimlane_id}")
def delete_swimlane_api(swimlane_id: int, user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    board = _board(db, user)
    swimlane = _get_swimlane(db, swimlane_id, board)
    if len(board.swimlanes) <= 1:
        raise HTTPException(status_code=400, detail="Je kunt niet de laatste swimlane van het bord verwijderen")
    db.delete(swimlane)
    db.commit()
    return _deleted(swimlane_id)
