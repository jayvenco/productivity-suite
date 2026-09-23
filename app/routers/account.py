from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from app.auth.dependencies import require_user
from app.auth.security import hash_password, verify_password
from app.config import settings
from app.database import Base, engine, get_db
from app.models.user import User
from app.routers.settings import AVAILABLE_BACKGROUNDS, AVAILABLE_DENSITIES, AVAILABLE_FONT_SIZES, AVAILABLE_FONTS
from app.services.api_tokens import generate_api_token, hash_api_token
from app.services.migrate import run_lightweight_migrations
from app.templating import templates

router = APIRouter(prefix="/account", tags=["account"])


def _sqlite_path_from_url(url: str) -> Path:
    """Leidt het bestandspad af uit settings.database_url i.p.v. een vast
    "app.db" aan te nemen -- moet ook kloppen als DATABASE_URL afwijkt (bv. in
    tests, die een eigen test.db gebruiken)."""
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise RuntimeError("Backup/restore wordt alleen voor SQLite ondersteund")
    return Path(url[len(prefix) :])


DB_PATH = _sqlite_path_from_url(settings.database_url)
# Tabellen die in elke versie van deze app al bestonden -- een backup die dit
# mist is geen (herkenbare) Productivity Suite-database.
_REQUIRED_TABLES = {"users", "tasks", "tags"}


def _appearance_context() -> dict:
    return {
        "available_fonts": AVAILABLE_FONTS,
        "available_font_sizes": AVAILABLE_FONT_SIZES,
        "available_densities": AVAILABLE_DENSITIES,
        "available_backgrounds": AVAILABLE_BACKGROUNDS,
    }


def _account_context(
    db: Session,
    user_id: int,
    *,
    error: str | None = None,
    success: str | None = None,
    new_api_token: str | None = None,
) -> dict:
    return {
        "error": error,
        "success": success,
        "new_api_token": new_api_token,
        **_appearance_context(),
    }


@router.get("")
def account_form(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "account/form.html", {"user": user, **_account_context(db, user.id)})


@router.post("")
def update_account(
    request: Request,
    current_password: str = Form(...),
    new_username: str = Form(...),
    new_password: str = Form(""),
    new_password_confirm: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Huidig wachtwoord klopt niet")},
            status_code=401,
        )

    if new_password and new_password != new_password_confirm:
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Nieuwe wachtwoorden komen niet overeen")},
            status_code=400,
        )

    existing = db.query(User).filter(User.username == new_username, User.id != user.id).first()
    if existing is not None:
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Gebruikersnaam is al in gebruik")},
            status_code=400,
        )

    user.username = new_username.strip()
    if new_password:
        user.password_hash = hash_password(new_password)
        user.using_default_password = False
    db.commit()

    return templates.TemplateResponse(
        request, "account/form.html", {"user": user, **_account_context(db, user.id, success="Opgeslagen")}
    )


# ---- API-token (voor externe agents/scripts, zie /api/v1/...) ----


@router.post("/api-token/generate")
def generate_api_token_route(
    request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    token = generate_api_token()
    user.api_token_hash = hash_api_token(token)
    db.commit()
    return templates.TemplateResponse(
        request, "account/form.html", {"user": user, **_account_context(db, user.id, new_api_token=token)}
    )


@router.post("/api-token/revoke")
def revoke_api_token_route(user: User = Depends(require_user), db: Session = Depends(get_db)):
    user.api_token_hash = None
    db.commit()
    return RedirectResponse("/account", status_code=303)


# ---- OpenAI API-sleutel (voor voice-commando-interpretatie, zie app/routers/voice.py) ----


@router.post("/openai-key")
def save_openai_key(
    openai_api_key: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if openai_api_key.strip():
        user.openai_api_key = openai_api_key.strip()
        db.commit()
    return RedirectResponse("/account", status_code=303)


@router.post("/openai-key/clear")
def clear_openai_key(user: User = Depends(require_user), db: Session = Depends(get_db)):
    user.openai_api_key = None
    db.commit()
    return RedirectResponse("/account", status_code=303)


@router.post("/openai-key/test")
async def test_openai_key(openai_api_key: str = Form(""), user: User = Depends(require_user)) -> dict:
    """Test de sleutel die in het formulierveld staat (nog niet per se opgeslagen) tegen
    de OpenAI API, i.p.v. altijd de al-opgeslagen sleutel -- zo kun je een nieuwe sleutel
    controleren vóórdat je 'm opslaat. Gebruikt het lichtste mogelijke endpoint
    (modellen opvragen) zodat testen geen tokens/kosten met zich meebrengt."""
    key = openai_api_key.strip() or (user.openai_api_key or "")
    if not key:
        return {"valid": False, "message": "Vul eerst een sleutel in."}

    try:
        async with httpx.AsyncClient(timeout=15) as http_client:
            response = await http_client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
            )
    except httpx.HTTPError:
        return {"valid": False, "message": "Kon geen verbinding maken met de OpenAI API."}

    if response.status_code == 200:
        return {"valid": True, "message": "Sleutel werkt."}
    if response.status_code == 401:
        return {"valid": False, "message": "Ongeldige sleutel (401 Unauthorized)."}
    return {"valid": False, "message": f"OpenAI gaf een foutmelding ({response.status_code})."}


# ---- Backup (export/import van de hele SQLite-database) ----


@router.get("/backup/export")
def export_backup(user: User = Depends(require_user)):
    """Exporteert een consistente snapshot via VACUUM INTO -- dat werkt veilig
    naast een lopende app (i.p.v. het live .db-bestand zelf kopiëren), en
    compact meteen mee."""
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(tmp_path)  # VACUUM INTO eist een doelpad dat nog niet bestaat

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("VACUUM INTO ?", (tmp_path,))
    finally:
        conn.close()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"productivity-suite-backup-{timestamp}.db"
    return FileResponse(
        tmp_path,
        filename=filename,
        media_type="application/octet-stream",
        background=BackgroundTask(os.remove, tmp_path),
    )


@router.post("/backup/import")
async def import_backup(
    request: Request,
    backup_file: UploadFile = File(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    contents = await backup_file.read()
    if not contents.startswith(b"SQLite format 3\x00"):
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Dit is geen geldig SQLite-databasebestand.")},
            status_code=400,
        )

    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    with os.fdopen(fd, "wb") as f:
        f.write(contents)

    try:
        check_conn = sqlite3.connect(tmp_path)
        try:
            tables = {row[0] for row in check_conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            check_conn.close()
    except sqlite3.DatabaseError:
        os.remove(tmp_path)
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Bestand kon niet als database gelezen worden.")},
            status_code=400,
        )

    if not _REQUIRED_TABLES.issubset(tables):
        os.remove(tmp_path)
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, **_account_context(db, user.id, error="Dit lijkt geen Productivity Suite-back-up te zijn.")},
            status_code=400,
        )

    # Deze request se eigen db-sessie moet dicht vóórdat we het bestand vervangen,
    # en de connectie-pool erna leeggemaakt zodat volgende requests het nieuwe
    # bestand oppikken i.p.v. een al-open handle naar het oude.
    db.close()
    engine.dispose()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safety_copy = DB_PATH.parent / f"{DB_PATH.name}.before-import-{timestamp}"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, safety_copy)
    shutil.move(tmp_path, DB_PATH)

    # De geïmporteerde back-up kan van een oudere appversie zijn -- vul
    # ontbrekende tabellen/kolommen aan zodat de huidige code er meteen mee werkt.
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations(engine)

    return RedirectResponse("/login", status_code=303)
