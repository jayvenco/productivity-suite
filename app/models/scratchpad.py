from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Scratchpad(Base):
    """Eén groot kladblok per gebruiker (HTML van de rich-text-editor): los van projecten en tags,
    voor snelle aantekeningen. Wordt automatisch opgeslagen."""

    __tablename__ = "scratchpads"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    content: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
