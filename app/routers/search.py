from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.calendar_event import CalendarEvent
from app.models.kanban import KanbanBoard, KanbanCard
from app.models.mindmap import MindmapBoard
from app.models.note import Note
from app.models.snippet import Snippet, SnippetFile
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    request: Request,
    q: str = "",
    tag: str = "",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Eén zoekscherm over alle taggable soorten items heen (taken, notities,
    kanban-kaarten, snippets, mindmaps, kalenderafspraken) -- op los woord (titel/
    inhoud) en/of op een specifieke tag, allebei tegelijk mag ook (AND)."""
    q = q.strip()
    tag = tag.strip()
    like = f"%{q}%" if q else None
    has_query = bool(q or tag)

    tasks: list[Task] = []
    notes: list[Note] = []
    cards: list[KanbanCard] = []
    snippets: list[Snippet] = []
    mindmaps: list[MindmapBoard] = []
    events: list[CalendarEvent] = []

    if has_query:
        task_query = db.query(Task).options(selectinload(Task.tags)).filter(Task.user_id == user.id)
        if tag:
            task_query = task_query.filter(Task.tags.any(Tag.name == tag))
        if like:
            task_query = task_query.filter(or_(Task.title.ilike(like), Task.description.ilike(like)))
        tasks = task_query.order_by(Task.created_at.desc()).all()

        note_query = db.query(Note).options(selectinload(Note.tags)).filter(Note.user_id == user.id)
        if tag:
            note_query = note_query.filter(Note.tags.any(Tag.name == tag))
        if like:
            note_query = note_query.filter(or_(Note.title.ilike(like), Note.content.ilike(like)))
        notes = note_query.order_by(Note.updated_at.desc()).all()

        card_query = (
            db.query(KanbanCard)
            .options(selectinload(KanbanCard.tags))
            .join(KanbanBoard, KanbanCard.board_id == KanbanBoard.id)
            .filter(KanbanBoard.user_id == user.id)
        )
        if tag:
            card_query = card_query.filter(KanbanCard.tags.any(Tag.name == tag))
        if like:
            card_query = card_query.filter(or_(KanbanCard.title.ilike(like), KanbanCard.description.ilike(like)))
        cards = card_query.order_by(KanbanCard.created_at.desc()).all()

        snippet_query = (
            db.query(Snippet)
            .options(selectinload(Snippet.tags), selectinload(Snippet.files))
            .filter(Snippet.user_id == user.id)
        )
        if tag:
            snippet_query = snippet_query.filter(Snippet.tags.any(Tag.name == tag))
        if like:
            snippet_query = snippet_query.filter(
                or_(Snippet.title.ilike(like), Snippet.files.any(SnippetFile.content.ilike(like)))
            )
        snippets = snippet_query.order_by(Snippet.updated_at.desc()).all()

        mindmap_query = (
            db.query(MindmapBoard).options(selectinload(MindmapBoard.tags)).filter(MindmapBoard.user_id == user.id)
        )
        if tag:
            mindmap_query = mindmap_query.filter(MindmapBoard.tags.any(Tag.name == tag))
        if like:
            mindmap_query = mindmap_query.filter(
                or_(MindmapBoard.name.ilike(like), MindmapBoard.description.ilike(like))
            )
        mindmaps = mindmap_query.order_by(MindmapBoard.id.desc()).all()

        event_query = (
            db.query(CalendarEvent).options(selectinload(CalendarEvent.tags)).filter(CalendarEvent.user_id == user.id)
        )
        if tag:
            event_query = event_query.filter(CalendarEvent.tags.any(Tag.name == tag))
        if like:
            event_query = event_query.filter(
                or_(CalendarEvent.title.ilike(like), CalendarEvent.description.ilike(like))
            )
        events = event_query.order_by(CalendarEvent.event_date.desc()).all()

    total = len(tasks) + len(notes) + len(cards) + len(snippets) + len(mindmaps) + len(events)
    all_tags = db.query(Tag).order_by(Tag.name).all()

    return templates.TemplateResponse(
        request,
        "search/results.html",
        {
            "user": user,
            "q": q,
            "tag": tag,
            "has_query": has_query,
            "total": total,
            "tasks": tasks,
            "notes": notes,
            "cards": cards,
            "snippets": snippets,
            "mindmaps": mindmaps,
            "events": events,
            "all_tags": all_tags,
        },
    )
