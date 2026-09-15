from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.kanban import KanbanBoard, KanbanCard, KanbanColumn, KanbanSwimlane
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/kanban", tags=["kanban"])


def _get_board_or_404(db: Session, user_id: int) -> KanbanBoard:
    board = (
        db.query(KanbanBoard)
        .options(selectinload(KanbanBoard.columns), selectinload(KanbanBoard.swimlanes))
        .filter(KanbanBoard.user_id == user_id)
        .first()
    )
    if board is None:
        raise HTTPException(status_code=404, detail="Geen kanbanbord gevonden")
    return board


@router.get("")
def board_view(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    board = _get_board_or_404(db, user.id)
    cards = (
        db.query(KanbanCard)
        .options(selectinload(KanbanCard.tags))
        .filter(KanbanCard.board_id == board.id)
        .order_by(KanbanCard.position)
        .all()
    )
    cards_by_column: dict[int, list[KanbanCard]] = {col.id: [] for col in board.columns}
    for card in cards:
        cards_by_column.setdefault(card.column_id, []).append(card)

    return templates.TemplateResponse(
        request,
        "kanban/board.html",
        {"user": user, "board": board, "cards_by_column": cards_by_column},
    )


@router.post("/cards")
def create_card(
    column_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, user.id)
    column = db.get(KanbanColumn, column_id)
    if column is None or column.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kolom niet gevonden")

    swimlane = db.query(KanbanSwimlane).filter(KanbanSwimlane.board_id == board.id).first()
    max_position = (
        db.query(KanbanCard).filter(KanbanCard.column_id == column_id).count()
    )

    card = KanbanCard(
        board_id=board.id,
        column_id=column_id,
        swimlane_id=swimlane.id,
        title=title.strip(),
        description=description,
        position=max_position,
    )
    card.tags = resolve_tags(db, tags)
    db.add(card)
    db.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/cards/{card_id}/move")
def move_card(
    card_id: int,
    column_id: int = Form(...),
    position: int = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Endpoint voor drag-and-drop: verplaatst een kaart naar een (mogelijk andere) kolom/positie."""
    board = _get_board_or_404(db, user.id)
    card = db.get(KanbanCard, card_id)
    if card is None or card.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")
    column = db.get(KanbanColumn, column_id)
    if column is None or column.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kolom niet gevonden")

    card.column_id = column_id
    card.position = position
    db.commit()
    return {"ok": True}


@router.post("/cards/{card_id}/delete")
def delete_card(card_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    board = _get_board_or_404(db, user.id)
    card = db.get(KanbanCard, card_id)
    if card is None or card.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")
    db.delete(card)
    db.commit()
    return RedirectResponse("/kanban", status_code=303)
