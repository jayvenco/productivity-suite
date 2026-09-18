from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MindmapBoard(Base):
    """Eén mindmap per gebruiker, net als het kanban-bord -- geen aparte
    board-beheer-UI nodig voor een "simpele mindmap"."""

    __tablename__ = "mindmap_boards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), default="Mindmap")

    nodes: Mapped[list["MindmapNode"]] = relationship(
        back_populates="board", cascade="all, delete-orphan"
    )
    edges: Mapped[list["MindmapEdge"]] = relationship(
        back_populates="board", cascade="all, delete-orphan"
    )


class MindmapNode(Base):
    """Los tekst-component op het canvas, vrij te verslepen (x/y in pixels
    t.o.v. de canvas-hoek) en van een eigen kleur te voorzien."""

    __tablename__ = "mindmap_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("mindmap_boards.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(200), default="Nieuw idee")
    color: Mapped[str] = mapped_column(String(20), default="#bd93f9")
    x: Mapped[int] = mapped_column(Integer, default=120)
    y: Mapped[int] = mapped_column(Integer, default=120)

    board: Mapped["MindmapBoard"] = relationship(back_populates="nodes")


class MindmapEdge(Base):
    """Verbinding tussen twee componenten. Puur een koppeling (geen eigen
    tekst/richting van betekenis) -- 'binden aan een ander steekwoord'."""

    __tablename__ = "mindmap_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("mindmap_boards.id", ondelete="CASCADE"), index=True)
    from_node_id: Mapped[int] = mapped_column(ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), index=True)
    to_node_id: Mapped[int] = mapped_column(ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), index=True)

    board: Mapped["MindmapBoard"] = relationship(back_populates="edges")
