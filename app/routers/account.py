from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.auth.security import hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.templating import templates

router = APIRouter(prefix="/account", tags=["account"])


@router.get("")
def account_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "account/form.html", {"user": user, "error": None, "success": None})


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
            {"user": user, "error": "Huidig wachtwoord klopt niet", "success": None},
            status_code=401,
        )

    if new_password and new_password != new_password_confirm:
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, "error": "Nieuwe wachtwoorden komen niet overeen", "success": None},
            status_code=400,
        )

    existing = db.query(User).filter(User.username == new_username, User.id != user.id).first()
    if existing is not None:
        return templates.TemplateResponse(
            request,
            "account/form.html",
            {"user": user, "error": "Gebruikersnaam is al in gebruik", "success": None},
            status_code=400,
        )

    user.username = new_username.strip()
    if new_password:
        user.password_hash = hash_password(new_password)
        user.using_default_password = False
    db.commit()

    return templates.TemplateResponse(
        request, "account/form.html", {"user": user, "error": None, "success": "Opgeslagen"}
    )
