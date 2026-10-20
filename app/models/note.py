from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import note_tags
from app.services.tags import first_tag_hue_style


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    is_temp: Mapped[bool] = mapped_column(Boolean, default=False)
    # Herkomst (zie NoteTemplate.version): alleen informatief. De notitie is een gewone,
    # zelfstandige notitie; verwijderen of wijzigen van het sjabloon raakt haar niet.
    template_id: Mapped[int | None] = mapped_column(ForeignKey("note_templates.id", ondelete="SET NULL"), nullable=True)
    template_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    template_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=note_tags, back_populates="notes"
    )

    @property
    def row_tint_style(self) -> str:
        """Zet --tag-hue op basis van de eerste tag (zie first_tag_hue_style) -- de
        standaard-thema's doen er niets mee, het "bubbles"-thema (themes/bubbles.css)
        gebruikt 'm voor een volle kleur op de notitiekaart."""
        return first_tag_hue_style(self.tags)
