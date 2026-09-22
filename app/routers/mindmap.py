from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.mindmap import MindmapBoard, MindmapEdge, MindmapNode
from app.models.tag import Tag
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/mindmap", tags=["mindmap"])

DEFAULT_COLOR = "#bd93f9"
DEFAULT_NAME = "Naamloze mindmap"


def _get_board_or_404(db: Session, board_id: int, user_id: int) -> MindmapBoard:
    board = db.query(MindmapBoard).filter(MindmapBoard.id == board_id, MindmapBoard.user_id == user_id).first()
    if board is None:
        raise HTTPException(status_code=404, detail="Mindmap niet gevonden")
    return board


def _get_node_or_404(db: Session, node_id: int, user_id: int) -> MindmapNode:
    """Zoekt een component op en checkt eigenaarschap via het bord (i.p.v. een
    los board_id in de URL) -- dat houdt de node-/edge-routes bruikbaar
    ongeacht in welke van de mindmaps van de gebruiker het component zit."""
    node = (
        db.query(MindmapNode)
        .join(MindmapBoard, MindmapNode.board_id == MindmapBoard.id)
        .filter(MindmapNode.id == node_id, MindmapBoard.user_id == user_id)
        .first()
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Component niet gevonden")
    return node


@router.get("")
def list_mindmaps(
    request: Request,
    tags: list[str] = Query(default=[]),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(MindmapBoard)
        .options(selectinload(MindmapBoard.tags))
        .filter(MindmapBoard.user_id == user.id)
    )
    if tags:
        query = query.filter(MindmapBoard.tags.any(Tag.name.in_(tags)))
    boards = query.order_by(MindmapBoard.id.desc()).all()

    node_counts = dict(
        db.query(MindmapNode.board_id, func.count(MindmapNode.id))
        .join(MindmapBoard, MindmapNode.board_id == MindmapBoard.id)
        .filter(MindmapBoard.user_id == user.id)
        .group_by(MindmapNode.board_id)
        .all()
    )
    all_tags = (
        db.query(Tag)
        .join(Tag.mindmaps)
        .filter(MindmapBoard.user_id == user.id)
        .distinct()
        .order_by(Tag.name)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "mindmap/list.html",
        {"user": user, "boards": boards, "node_counts": node_counts, "all_tags": all_tags, "active_tags": tags},
    )


@router.post("")
def create_mindmap(
    name: str = Form(DEFAULT_NAME),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = MindmapBoard(user_id=user.id, name=name.strip() or DEFAULT_NAME, description=description)
    board.tags = resolve_tags(db, tags)
    db.add(board)
    db.flush()
    db.add(MindmapNode(board_id=board.id, text="Hoofdonderwerp", color=DEFAULT_COLOR, x=40, y=40))
    db.commit()
    return RedirectResponse(f"/mindmap/{board.id}", status_code=303)


@router.post("/{board_id}/update")
def update_mindmap_metadata(
    board_id: int,
    name: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, board_id, user.id)
    board.name = name.strip() or board.name
    board.description = description
    board.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/mindmap", status_code=303)


@router.get("/{board_id}")
def mindmap_view(
    board_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    board = _get_board_or_404(db, board_id, user.id)
    nodes = db.query(MindmapNode).filter(MindmapNode.board_id == board.id).all()
    edges = db.query(MindmapEdge).filter(MindmapEdge.board_id == board.id).all()
    return templates.TemplateResponse(
        request, "mindmap/board.html", {"user": user, "board": board, "nodes": nodes, "edges": edges}
    )


@router.post("/{board_id}/rename")
def rename_mindmap(
    board_id: int, name: str = Form(...), user: User = Depends(require_user), db: Session = Depends(get_db)
):
    board = _get_board_or_404(db, board_id, user.id)
    board.name = name.strip() or board.name
    db.commit()
    return {"id": board.id, "name": board.name}


@router.post("/{board_id}/delete")
def delete_mindmap(board_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    board = _get_board_or_404(db, board_id, user.id)
    db.delete(board)
    db.commit()
    return RedirectResponse("/mindmap", status_code=303)


@router.post("/{board_id}/nodes")
def create_node(
    board_id: int,
    text: str = Form("Nieuw idee"),
    color: str = Form(DEFAULT_COLOR),
    x: int = Form(120),
    y: int = Form(120),
    parent_id: int | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, board_id, user.id)
    node = MindmapNode(board_id=board.id, text=(text.strip() or "Nieuw idee"), color=color, x=x, y=y)
    db.add(node)
    db.flush()

    edge = None
    if parent_id is not None:
        parent = db.query(MindmapNode).filter(MindmapNode.id == parent_id, MindmapNode.board_id == board.id).first()
        if parent is not None:
            edge = MindmapEdge(board_id=board.id, from_node_id=parent.id, to_node_id=node.id)
            db.add(edge)
            db.flush()

    db.commit()
    return {
        "id": node.id,
        "text": node.text,
        "color": node.color,
        "x": node.x,
        "y": node.y,
        "edge": {"id": edge.id, "from_node_id": edge.from_node_id, "to_node_id": edge.to_node_id} if edge else None,
    }


@router.post("/nodes/{node_id}")
def update_node(
    node_id: int,
    text: str | None = Form(None),
    color: str | None = Form(None),
    x: int | None = Form(None),
    y: int | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    node = _get_node_or_404(db, node_id, user.id)

    if text is not None:
        node.text = text.strip() or node.text
    if color is not None:
        node.color = color
    if x is not None:
        node.x = x
    if y is not None:
        node.y = y
    db.commit()
    return {"id": node.id, "text": node.text, "color": node.color, "x": node.x, "y": node.y}


@router.post("/nodes/{node_id}/delete")
def delete_node(node_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    node = _get_node_or_404(db, node_id, user.id)
    board_id = node.board_id

    db.query(MindmapEdge).filter(
        MindmapEdge.board_id == board_id,
        (MindmapEdge.from_node_id == node_id) | (MindmapEdge.to_node_id == node_id),
    ).delete(synchronize_session=False)
    db.delete(node)
    db.commit()
    return {"ok": True}


@router.post("/edges")
def create_edge(
    from_node_id: int = Form(...),
    to_node_id: int = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if from_node_id == to_node_id:
        raise HTTPException(status_code=400, detail="Kan een component niet met zichzelf verbinden")

    from_node = _get_node_or_404(db, from_node_id, user.id)
    to_node = _get_node_or_404(db, to_node_id, user.id)
    if from_node.board_id != to_node.board_id:
        raise HTTPException(status_code=400, detail="Componenten moeten in dezelfde mindmap zitten")

    board_id = from_node.board_id
    existing = (
        db.query(MindmapEdge)
        .filter(
            MindmapEdge.board_id == board_id,
            (
                ((MindmapEdge.from_node_id == from_node_id) & (MindmapEdge.to_node_id == to_node_id))
                | ((MindmapEdge.from_node_id == to_node_id) & (MindmapEdge.to_node_id == from_node_id))
            ),
        )
        .first()
    )
    if existing is not None:
        return {"id": existing.id, "from_node_id": existing.from_node_id, "to_node_id": existing.to_node_id}

    edge = MindmapEdge(board_id=board_id, from_node_id=from_node_id, to_node_id=to_node_id)
    db.add(edge)
    db.commit()
    return {"id": edge.id, "from_node_id": edge.from_node_id, "to_node_id": edge.to_node_id}


@router.post("/edges/{edge_id}/delete")
def delete_edge(edge_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    edge = (
        db.query(MindmapEdge)
        .join(MindmapBoard, MindmapEdge.board_id == MindmapBoard.id)
        .filter(MindmapEdge.id == edge_id, MindmapBoard.user_id == user.id)
        .first()
    )
    if edge is None:
        raise HTTPException(status_code=404, detail="Verbinding niet gevonden")
    db.delete(edge)
    db.commit()
    return {"ok": True}
