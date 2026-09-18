from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.mindmap import MindmapBoard, MindmapEdge, MindmapNode
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/mindmap", tags=["mindmap"])

DEFAULT_COLOR = "#bd93f9"


def _get_or_create_board(db: Session, user_id: int) -> MindmapBoard:
    board = db.query(MindmapBoard).filter(MindmapBoard.user_id == user_id).first()
    if board is None:
        board = MindmapBoard(user_id=user_id, name="Mindmap")
        db.add(board)
        db.flush()
        db.add(
            MindmapNode(board_id=board.id, text="Hoofdonderwerp", color=DEFAULT_COLOR, x=40, y=40)
        )
        db.commit()
        db.refresh(board)
    return board


def _get_node_or_404(db: Session, node_id: int, board_id: int) -> MindmapNode:
    node = db.query(MindmapNode).filter(MindmapNode.id == node_id, MindmapNode.board_id == board_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Component niet gevonden")
    return node


@router.get("")
def mindmap_view(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    board = _get_or_create_board(db, user.id)
    nodes = db.query(MindmapNode).filter(MindmapNode.board_id == board.id).all()
    edges = db.query(MindmapEdge).filter(MindmapEdge.board_id == board.id).all()
    return templates.TemplateResponse(
        request, "mindmap/board.html", {"user": user, "board": board, "nodes": nodes, "edges": edges}
    )


@router.post("/nodes")
def create_node(
    text: str = Form("Nieuw idee"),
    color: str = Form(DEFAULT_COLOR),
    x: int = Form(120),
    y: int = Form(120),
    parent_id: int | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_or_create_board(db, user.id)
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
    board = _get_or_create_board(db, user.id)
    node = _get_node_or_404(db, node_id, board.id)

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
    board = _get_or_create_board(db, user.id)
    node = _get_node_or_404(db, node_id, board.id)

    db.query(MindmapEdge).filter(
        MindmapEdge.board_id == board.id,
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
    board = _get_or_create_board(db, user.id)
    if from_node_id == to_node_id:
        raise HTTPException(status_code=400, detail="Kan een component niet met zichzelf verbinden")

    _get_node_or_404(db, from_node_id, board.id)
    _get_node_or_404(db, to_node_id, board.id)

    existing = (
        db.query(MindmapEdge)
        .filter(
            MindmapEdge.board_id == board.id,
            (
                ((MindmapEdge.from_node_id == from_node_id) & (MindmapEdge.to_node_id == to_node_id))
                | ((MindmapEdge.from_node_id == to_node_id) & (MindmapEdge.to_node_id == from_node_id))
            ),
        )
        .first()
    )
    if existing is not None:
        return {"id": existing.id, "from_node_id": existing.from_node_id, "to_node_id": existing.to_node_id}

    edge = MindmapEdge(board_id=board.id, from_node_id=from_node_id, to_node_id=to_node_id)
    db.add(edge)
    db.commit()
    return {"id": edge.id, "from_node_id": edge.from_node_id, "to_node_id": edge.to_node_id}


@router.post("/edges/{edge_id}/delete")
def delete_edge(edge_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    board = _get_or_create_board(db, user.id)
    edge = db.query(MindmapEdge).filter(MindmapEdge.id == edge_id, MindmapEdge.board_id == board.id).first()
    if edge is None:
        raise HTTPException(status_code=404, detail="Verbinding niet gevonden")
    db.delete(edge)
    db.commit()
    return {"ok": True}
