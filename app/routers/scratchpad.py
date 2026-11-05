from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.scratchpad import Scratchpad
from app.models.user import User
from app.services.richtext import sanitize_rich
from app.templating import templates

router = APIRouter(prefix="/scratchpad", tags=["scratchpad"])


def get_pad(db: Session, user_id: int) -> Scratchpad:
    pad = db.get(Scratchpad, user_id)
    if pad is None:
        pad = Scratchpad(user_id=user_id, content="")
        db.add(pad)
        db.commit()
        db.refresh(pad)
    return pad


@router.get("")
def scratchpad_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    pad = get_pad(db, user.id)
    return templates.TemplateResponse(request, "scratchpad/page.html", {"user": user, "pad": pad})


@router.post("")
def save_scratchpad(
    content: str = Form(""), user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """Automatisch opslaan vanuit de editor (fetch/sendBeacon); geeft het opslagmoment terug."""
    pad = get_pad(db, user.id)
    pad.content = sanitize_rich(content)
    db.commit()
    db.refresh(pad)
    return {"ok": True, "saved_at": pad.updated_at.isoformat()}
