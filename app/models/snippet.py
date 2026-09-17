from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import snippet_tags


class Snippet(Base):
    __tablename__ = "snippets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    files: Mapped[list["SnippetFile"]] = relationship(
        back_populates="snippet", cascade="all, delete-orphan", order_by="SnippetFile.position"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=snippet_tags, back_populates="snippets"
    )

    @property
    def row_tint_style(self) -> str:
        """Zelfde patroon als Task/Note.row_tint_style: lichte tint van de eerste tag."""
        if not self.tags:
            return ""
        hue = self.tags[0].hue
        if hue is None:
            return ""
        return f"background-color: hsla({hue}, 60%, 50%, 0.08);"


class SnippetFile(Base):
    """Eén bestand/fragment binnen een snippet -- een snippet kan er meerdere hebben
    (bv. main.py + requirements.txt bij elkaar), zoals bij ByteStash."""

    __tablename__ = "snippet_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    snippet_id: Mapped[int] = mapped_column(ForeignKey("snippets.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(40), default="plaintext")
    content: Mapped[str] = mapped_column(Text, default="")
    position: Mapped[int] = mapped_column(Integer, default=0)

    snippet: Mapped["Snippet"] = relationship(back_populates="files")
