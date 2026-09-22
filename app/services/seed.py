from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.config import settings
from app.models.kanban import KanbanBoard, KanbanColumn, KanbanSwimlane
from app.models.user import User

DEFAULT_COLUMNS = ["Backlog", "Todo", "In Progress", "Done"]
DEFAULT_SWIMLANE = "Algemeen"


def seed_default_user_and_board(db: Session) -> None:
    """Single-user setup: maakt bij lege database het admin-account en een
    standaard kanbanbord met kolommen aan."""
    if db.query(User).count() > 0:
        return

    user = User(
        username=settings.default_username,
        password_hash=hash_password(settings.default_password),
        theme=settings.default_theme,
    )
    db.add(user)
    db.flush()

    board = KanbanBoard(user_id=user.id, name="Mijn bord")
    db.add(board)
    db.flush()

    swimlane = KanbanSwimlane(board_id=board.id, name=DEFAULT_SWIMLANE, position=0)
    db.add(swimlane)
    db.flush()

    for position, name in enumerate(DEFAULT_COLUMNS):
        db.add(KanbanColumn(board_id=board.id, swimlane_id=swimlane.id, name=name, position=position))

    db.commit()
