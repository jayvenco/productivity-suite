from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.kanban import KanbanBoard, KanbanCard, KanbanColumn, KanbanSwimlane
from app.models.user import User
from app.services.checklist import toggle_checklist_line
from app.services.seed import DEFAULT_COLUMNS
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/kanban", tags=["kanban"])


def _get_board_or_404(db: Session, user_id: int) -> KanbanBoard:
    board = (
        db.query(KanbanBoard)
        .options(selectinload(KanbanBoard.swimlanes).selectinload(KanbanSwimlane.columns))
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
    cards_by_cell: dict[tuple[int, int], list[KanbanCard]] = {}
    for card in cards:
        cards_by_cell.setdefault((card.swimlane_id, card.column_id), []).append(card)

    return templates.TemplateResponse(
        request,
        "kanban/board.html",
        {"user": user, "board": board, "cards_by_cell": cards_by_cell},
    )


@router.post("/swimlanes")
def create_swimlane(
    name: str = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Elke swimlane krijgt haar eigen set standaardkolommen, die daarna onafhankelijk
    van andere swimlanes aan te passen is (zie create_column)."""
    board = _get_board_or_404(db, user.id)
    position = len(board.swimlanes)
    swimlane = KanbanSwimlane(board_id=board.id, name=name.strip(), position=position)
    db.add(swimlane)
    db.flush()

    for col_position, col_name in enumerate(DEFAULT_COLUMNS):
        db.add(
            KanbanColumn(board_id=board.id, swimlane_id=swimlane.id, name=col_name, position=col_position)
        )

    db.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/swimlanes/{swimlane_id}/columns")
def create_column(
    swimlane_id: int,
    name: str = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, user.id)
    swimlane = db.get(KanbanSwimlane, swimlane_id)
    if swimlane is None or swimlane.board_id != board.id:
        raise HTTPException(status_code=404, detail="Swimlane niet gevonden")

    position = len(swimlane.columns)
    db.add(KanbanColumn(board_id=board.id, swimlane_id=swimlane_id, name=name.strip(), position=position))
    db.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/cards")
def create_card(
    column_id: int = Form(...),
    swimlane_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, user.id)
    swimlane = db.get(KanbanSwimlane, swimlane_id)
    if swimlane is None or swimlane.board_id != board.id:
        raise HTTPException(status_code=404, detail="Swimlane niet gevonden")
    column = db.get(KanbanColumn, column_id)
    if column is None or column.swimlane_id != swimlane_id:
        raise HTTPException(status_code=404, detail="Kolom niet gevonden")

    max_position = (
        db.query(KanbanCard)
        .filter(KanbanCard.column_id == column_id, KanbanCard.swimlane_id == swimlane_id)
        .count()
    )

    card = KanbanCard(
        board_id=board.id,
        column_id=column_id,
        swimlane_id=swimlane_id,
        title=title.strip(),
        description=description,
        position=max_position,
    )
    card.tags = resolve_tags(db, tags)
    db.add(card)
    db.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/cards/{card_id}")
def update_card(
    card_id: int,
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    color: str = Form(""),
    clear_color: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    board = _get_board_or_404(db, user.id)
    card = db.get(KanbanCard, card_id)
    if card is None or card.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")

    card.title = title.strip()
    card.description = description
    card.color = None if clear_color or not color else color
    card.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/kanban", status_code=303)


@router.post("/cards/{card_id}/move")
def move_card(
    card_id: int,
    column_id: int = Form(...),
    swimlane_id: int = Form(...),
    position: int = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Endpoint voor drag-and-drop: verplaatst een kaart naar een (mogelijk andere) cel
    (kolom x swimlane) en positie."""
    board = _get_board_or_404(db, user.id)
    card = db.get(KanbanCard, card_id)
    if card is None or card.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")
    swimlane = db.get(KanbanSwimlane, swimlane_id)
    if swimlane is None or swimlane.board_id != board.id:
        raise HTTPException(status_code=404, detail="Swimlane niet gevonden")
    column = db.get(KanbanColumn, column_id)
    if column is None or column.swimlane_id != swimlane_id:
        raise HTTPException(status_code=404, detail="Kolom niet gevonden")

    card.column_id = column_id
    card.swimlane_id = swimlane_id
    card.position = position
    db.commit()
    return {"ok": True}


@router.post("/cards/{card_id}/checklist-toggle")
def toggle_checklist(
    card_id: int,
    line_index: int = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Vinkt een regel '- [ ] ...' / '- [x] ...' in de kaartbeschrijving aan/uit."""
    board = _get_board_or_404(db, user.id)
    card = db.get(KanbanCard, card_id)
    if card is None or card.board_id != board.id:
        raise HTTPException(status_code=404, detail="Kaart niet gevonden")

    card.description = toggle_checklist_line(card.description, line_index)
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
