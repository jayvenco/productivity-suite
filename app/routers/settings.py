from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

AVAILABLE_THEMES = ["dracula", "one-dark-pro", "nord"]


@router.post("/theme")
def set_theme(
    theme: str = Form(...),
    redirect_to: str = Form("/"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if theme in AVAILABLE_THEMES:
        user.theme = theme
        db.commit()
    return RedirectResponse(redirect_to, status_code=303)
