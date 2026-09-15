from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import card_tags


class KanbanBoard(Base):
    __tablename__ = "kanban_boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))

    columns: Mapped[list["KanbanColumn"]] = relationship(
        back_populates="board", cascade="all, delete-orphan", order_by="KanbanColumn.position"
    )
    swimlanes: Mapped[list["KanbanSwimlane"]] = relationship(
        back_populates="board", cascade="all, delete-orphan", order_by="KanbanSwimlane.position"
    )


class KanbanColumn(Base):
    """Een kolom = status (bv. Todo/In Progress/Done), aanpasbaar per bord."""

    __tablename__ = "kanban_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("kanban_boards.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer, default=0)

    board: Mapped["KanbanBoard"] = relationship(back_populates="columns")
    cards: Mapped[list["KanbanCard"]] = relationship(back_populates="column")


class KanbanSwimlane(Base):
    """Extra dimensie (bv. project/context). In Fase 1 heeft elk bord één 'Algemeen'
    swimlane en toont de UI geen swimlane-indeling; het model bestaat al zodat
    Fase 2 geen destructieve migratie nodig heeft."""

    __tablename__ = "kanban_swimlanes"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("kanban_boards.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer, default=0)

    board: Mapped["KanbanBoard"] = relationship(back_populates="swimlanes")
    cards: Mapped[list["KanbanCard"]] = relationship(back_populates="swimlane")


class KanbanCard(Base):
    """Losse entiteit (geen 1-op-1 met Task): een kaart kan optioneel naar een
    Task verwijzen, maar hoeft dat niet -- zie architectuurbeslissing."""

    __tablename__ = "kanban_cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("kanban_boards.id", ondelete="CASCADE"), index=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("kanban_columns.id", ondelete="CASCADE"), index=True)
    swimlane_id: Mapped[int] = mapped_column(ForeignKey("kanban_swimlanes.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    board: Mapped["KanbanBoard"] = relationship()
    column: Mapped["KanbanColumn"] = relationship(back_populates="cards")
    swimlane: Mapped["KanbanSwimlane"] = relationship(back_populates="cards")
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=card_tags, back_populates="cards"
    )
