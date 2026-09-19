from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.kanban import KanbanBoard, KanbanColumn, KanbanSwimlane
from app.services.seed import DEFAULT_COLUMNS, DEFAULT_SWIMLANE


def get_or_create_default_cell(db: Session, board: KanbanBoard) -> tuple[KanbanSwimlane, KanbanColumn]:
    """Zonder opgegeven swimlane/kolom gebruiken we de eerste swimlane en diens
    eerste kolom -- zodat een kaart aangemaakt kan worden zonder eerst de
    kanban-structuur te hoeven opvragen (agent-API en snelle quick-add)."""
    swimlane = (
        db.query(KanbanSwimlane)
        .filter(KanbanSwimlane.board_id == board.id)
        .order_by(KanbanSwimlane.position)
        .first()
    )
    if swimlane is None:
        swimlane = KanbanSwimlane(board_id=board.id, name=DEFAULT_SWIMLANE, position=0)
        db.add(swimlane)
        db.flush()
        for position, name in enumerate(DEFAULT_COLUMNS):
            db.add(KanbanColumn(board_id=board.id, swimlane_id=swimlane.id, name=name, position=position))
        db.flush()

    column = (
        db.query(KanbanColumn)
        .filter(KanbanColumn.swimlane_id == swimlane.id)
        .order_by(KanbanColumn.position)
        .first()
    )
    return swimlane, column
