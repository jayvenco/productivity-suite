from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class InboxItem(Base):
    """Snel ingetypte tekst die later (als er tijd voor is) een notitie, taak of kanban-kaart
    wordt. De eerste regel wordt dan de titel, de rest de beschrijving/inhoud."""

    __tablename__ = "inbox_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
