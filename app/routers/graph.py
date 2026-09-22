from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.kanban import KanbanBoard, KanbanCard
from app.models.mindmap import MindmapBoard
from app.models.note import Note
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("")
def graph_view(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "graph/view.html", {"user": user})


@router.get("/data")
def graph_data(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Bipartiet graaf: elk getagd item (taak/notitie/kanban-kaart/mindmap) krijgt
    een edge naar elke tag die het heeft. Items zonder tags kunnen met niets
    linken en worden dus weggelaten -- dit is een taggraaf, geen volledige
    lijst van alle items (die staat al op de eigen overzichtspagina's)."""
    nodes: list[dict] = []
    edges: list[dict] = []
    tag_node_ids: dict[int, str] = {}

    def tag_node(tag: Tag) -> str:
        node_id = tag_node_ids.get(tag.id)
        if node_id is None:
            node_id = f"tag-{tag.id}"
            tag_node_ids[tag.id] = node_id
            nodes.append({"id": node_id, "type": "tag", "label": f"#{tag.name}", "url": None})
        return node_id

    tasks = db.query(Task).options(selectinload(Task.tags)).filter(Task.user_id == user.id).all()
    for task in tasks:
        if not task.tags:
            continue
        node_id = f"task-{task.id}"
        nodes.append({"id": node_id, "type": "task", "label": task.title, "url": f"/tasks/{task.id}/edit"})
        for tag in task.tags:
            edges.append({"source": node_id, "target": tag_node(tag)})

    notes = db.query(Note).options(selectinload(Note.tags)).filter(Note.user_id == user.id).all()
    for note in notes:
        if not note.tags:
            continue
        node_id = f"note-{note.id}"
        nodes.append({"id": node_id, "type": "note", "label": note.title, "url": f"/notes/{note.id}/edit"})
        for tag in note.tags:
            edges.append({"source": node_id, "target": tag_node(tag)})

    cards = (
        db.query(KanbanCard)
        .options(selectinload(KanbanCard.tags))
        .join(KanbanBoard, KanbanCard.board_id == KanbanBoard.id)
        .filter(KanbanBoard.user_id == user.id)
        .all()
    )
    for card in cards:
        if not card.tags:
            continue
        node_id = f"card-{card.id}"
        nodes.append({"id": node_id, "type": "kanban", "label": card.title, "url": "/kanban"})
        for tag in card.tags:
            edges.append({"source": node_id, "target": tag_node(tag)})

    boards = (
        db.query(MindmapBoard).options(selectinload(MindmapBoard.tags)).filter(MindmapBoard.user_id == user.id).all()
    )
    for board in boards:
        if not board.tags:
            continue
        node_id = f"mindmap-{board.id}"
        nodes.append({"id": node_id, "type": "mindmap", "label": board.name, "url": f"/mindmap/{board.id}"})
        for tag in board.tags:
            edges.append({"source": node_id, "target": tag_node(tag)})

    return {"nodes": nodes, "edges": edges}
