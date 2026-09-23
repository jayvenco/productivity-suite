from __future__ import annotations

import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
# Overrideable via DATA_DIR env var (bv. door tests) -- productie/Docker gebruikt gewoon
# de default, geen configuratie nodig.
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY_FILE = DATA_DIR / ".secret_key"


def _load_or_create_secret_key() -> str:
    """Genereert bij de allereerste start een willekeurige secret key en bewaart die
    in het data-volume, zodat er geen .env of omgevingsvariabele nodig is en sessies
    geldig blijven na een container-herstart/update."""
    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_text().strip()

    key = secrets.token_hex(32)
    SECRET_KEY_FILE.write_text(key)
    SECRET_KEY_FILE.chmod(0o600)
    return key


class Settings(BaseSettings):
    # Geen env_file: alle configuratie werkt met ingebouwde defaults zodat de app
    # zonder .env of extra omgevingsvariabelen draait (handig voor bv. Unraid).
    model_config = SettingsConfigDict()

    app_name: str = "Productivity Suite"
    database_url: str = f"sqlite:///{DATA_DIR / 'app.db'}"
    secret_key: str = ""  # wordt hieronder ingevuld vanuit _load_or_create_secret_key()
    session_cookie_name: str = "ps_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # 30 dagen

    # Single-user auth: seed-account met vaste standaard-inloggegevens. Wachtwoord
    # wijzigen kan via de "Account"-pagina in de app zelf.
    default_username: str = "admin"
    default_password: str = "admin"

    default_theme: str = "dracula"

    pomodoro_work_minutes: int = 25
    pomodoro_break_minutes: int = 5

    # Losse, self-hosted Whisper-container (bv. onedr0p/whisper-asr-webservice) voor
    # lokale spraak-naar-tekst -- overridebaar via WHISPER_SERVICE_URL env var, zodat
    # de container-naam/poort op Unraid vrij te kiezen is zonder codewijziging.
    whisper_service_url: str = "http://whisper:9000"


settings = Settings()
settings.secret_key = _load_or_create_secret_key()
