from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Expliciete association-tabellen per taggable type (i.p.v. polymorfe FK) --
# simpeler met SQLAlchemy en houdt referentiele integriteit per tabel.
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

card_tags = Table(
    "card_tags",
    Base.metadata,
    Column("card_id", ForeignKey("kanban_cards.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Fase 3 voegt note_tags en snippet_tags toe zodra de Note/Snippet modellen bestaan.


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(20), default="#6c7086")

    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", secondary=task_tags, back_populates="tags"
    )
    cards: Mapped[list["KanbanCard"]] = relationship(  # noqa: F821
        "KanbanCard", secondary=card_tags, back_populates="tags"
    )
