from __future__ import annotations

import re

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

_HSL_HUE_RE = re.compile(r"hsl\(\s*(\d+)")

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

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

snippet_tags = Table(
    "snippet_tags",
    Base.metadata,
    Column("snippet_id", ForeignKey("snippets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

event_tags = Table(
    "event_tags",
    Base.metadata,
    Column("event_id", ForeignKey("calendar_events.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

mindmap_tags = Table(
    "mindmap_tags",
    Base.metadata,
    Column("mindmap_board_id", ForeignKey("mindmap_boards.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(30), default="#6c7086")

    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", secondary=task_tags, back_populates="tags"
    )
    cards: Mapped[list["KanbanCard"]] = relationship(  # noqa: F821
        "KanbanCard", secondary=card_tags, back_populates="tags"
    )
    notes: Mapped[list["Note"]] = relationship(  # noqa: F821
        "Note", secondary=note_tags, back_populates="tags"
    )
    snippets: Mapped[list["Snippet"]] = relationship(  # noqa: F821
        "Snippet", secondary=snippet_tags, back_populates="tags"
    )
    events: Mapped[list["CalendarEvent"]] = relationship(  # noqa: F821
        "CalendarEvent", secondary=event_tags, back_populates="tags"
    )
    mindmaps: Mapped[list["MindmapBoard"]] = relationship(  # noqa: F821
        "MindmapBoard", secondary=mindmap_tags, back_populates="tags"
    )

    @property
    def hue(self) -> int | None:
        """Tint (0-359) uit de opgeslagen 'hsl(H, S%, L%)'-kleur, of None als de
        kleur niet in dat formaat staat (bv. een oude/handmatige hex-waarde)."""
        match = _HSL_HUE_RE.match(self.color or "")
        return int(match.group(1)) if match else None

    @property
    def badge_style(self) -> str:
        """Stijl voor het tag-label zelf: een duidelijk gekleurde rand + lichte vulling.
        Zet de tint als CSS custom property (--tag-hue) i.p.v. een kant-en-klare
        background-color, zodat een thema (zie .tag[style*="--tag-hue"] in app.css)
        zelf kan bepalen hoe transparant/solide de vulling is via --tag-alpha/
        --tag-lightness, zonder dat elke template die badge_style gebruikt hoeft
        te weten welk thema actief is."""
        if self.hue is None:
            return ""
        return f"--tag-hue: {self.hue}; border-color: hsl({self.hue}, 55%, 45%);"
