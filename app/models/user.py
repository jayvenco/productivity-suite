from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    theme: Mapped[str] = mapped_column(String(50), default="dracula")
    font_family: Mapped[str] = mapped_column(String(50), default="system")
    font_size: Mapped[int] = mapped_column(Integer, default=14)
    density: Mapped[str] = mapped_column(String(20), default="comfortable")
    # True zolang het wachtwoord nog het seed-standaardwachtwoord is -- stuurt de
    # waarschuwingsbanner die aanzet tot wachtwoord wijzigen via /account.
    using_default_password: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
