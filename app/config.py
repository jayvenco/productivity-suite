from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Productivity Suite"
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"
    secret_key: str = "change-me-in-production"
    session_cookie_name: str = "ps_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # 30 dagen

    # Single-user auth: inloggegevens worden bij eerste start geseed als er nog geen user is.
    default_username: str = "admin"
    default_password: str = "changeme"

    default_theme: str = "dracula"

    pomodoro_work_minutes: int = 25
    pomodoro_break_minutes: int = 5


settings = Settings()
