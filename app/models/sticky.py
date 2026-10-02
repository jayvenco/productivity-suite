from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import sticky_tags

STICKY_COLORS = ["yellow", "pink", "blue", "green", "orange", "purple"]


class Sticky(Base):
    """Plakbriefje: korte platte tekst met een eigen kleur, optioneel getagd, en
    optioneel "temp" (wordt na een week automatisch verwijderd, net als tijdelijke notities)."""

    __tablename__ = "stickies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    color: Mapped[str] = mapped_column(String(20), default="yellow")
    is_temp: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=sticky_tags, back_populates="stickies"
    )
