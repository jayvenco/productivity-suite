from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def _loads(raw: str | None, default):
    try:
        return json.loads(raw) if raw else default
    except ValueError:
        return default


class NoteModule(Base):
    """Herbruikbare inhoudsmodule (bibliotheek). `type` verwijst naar het register in
    app/services/note_templates.py (MODULE_TYPES); `config` is JSON (bv. de veldlijst van een
    "fields"-module). user_id NULL = ingebouwd."""

    __tablename__ = "note_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[str] = mapped_column(Text, default="{}")
    default_content: Mapped[str] = mapped_column(Text, default="")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def config_dict(self) -> dict:
        return _loads(self.config, {})


class NoteTemplate(Base):
    __tablename__ = "note_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    builtin_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), default="Kennis & documentatie")
    icon: Mapped[str] = mapped_column(String(10), default="📝")
    tags: Mapped[str] = mapped_column(String(200), default="")  # komma-gescheiden, zoals elders
    title_pattern: Mapped[str] = mapped_column(String(200), default="{{title}}")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    # Gaat omhoog bij elke wijziging; een gegenereerde notitie onthoudt de versie waarmee ze
    # gemaakt is (Note.template_version) maar blijft verder volledig zelfstandig.
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    modules: Mapped[list["NoteTemplateModule"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="NoteTemplateModule.position"
    )


class NoteTemplateModule(Base):
    """Eén plek van een module binnen een sjabloon (dezelfde module mag er meerdere keren in
    staan): volgorde, eigen titel, optioneel-vlag en eventuele afwijkende standaardtekst/config."""

    __tablename__ = "note_template_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("note_templates.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("note_modules.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(150), default="")
    optional: Mapped[bool] = mapped_column(Boolean, default=False)
    default_content: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[str] = mapped_column(Text, default="")  # JSON-override; leeg = die van de module

    template: Mapped["NoteTemplate"] = relationship(back_populates="modules")
    module: Mapped["NoteModule"] = relationship()

    @property
    def effective_config(self) -> dict:
        base = self.module.config_dict
        override = _loads(self.config, {})
        return {**base, **override} if isinstance(override, dict) else base

    @property
    def effective_title(self) -> str:
        return self.title or self.module.name

    @property
    def effective_default(self) -> str:
        return self.default_content or self.module.default_content
