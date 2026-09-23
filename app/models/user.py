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
    background: Mapped[str] = mapped_column(String(30), default="none")
    background_opacity: Mapped[int] = mapped_column(Integer, default=30)
    # True zolang het wachtwoord nog het seed-standaardwachtwoord is -- stuurt de
    # waarschuwingsbanner die aanzet tot wachtwoord wijzigen via /account.
    using_default_password: Mapped[bool] = mapped_column(Boolean, default=True)
    # SHA-256-hash van het API-token (nooit het token zelf) -- zelfde patroon als
    # password_hash. None zolang er geen token gegenereerd is.
    api_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # In tegenstelling tot api_token_hash bewust WEL leesbaar opgeslagen (niet gehasht):
    # de app moet 'm zelf meesturen bij calls naar de OpenAI API voor de
    # voice-commando-interpretatie, dus een hash (die je niet kunt terugdraaien) volstaat
    # hier niet. Blijft binnen de eigen SQLite-database, wordt nooit naar de client gestuurd.
    openai_api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
