from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.sticky import STICKY_COLORS, Sticky
from app.models.tag import Tag
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/stickies", tags=["stickies"])

TEMP_STICKY_LIFETIME = timedelta(days=7)

STICKY_COLOR_LABELS = {
    "yellow": "Geel",
    "pink": "Roze",
    "blue": "Blauw",
    "green": "Groen",
    "orange": "Oranje",
    "purple": "Paars",
}


def _delete_expired_temp_stickies(db: Session, user_id: int) -> None:
    """Zelfde opportunistische opruiming bij elk bezoek als tijdelijke notities."""
    cutoff = datetime.now(UTC).replace(tzinfo=None) - TEMP_STICKY_LIFETIME
    db.query(Sticky).filter(
        Sticky.user_id == user_id, Sticky.is_temp.is_(True), Sticky.created_at < cutoff
    ).delete(synchronize_session=False)
    db.commit()


def _get_sticky_or_404(db: Session, sticky_id: int, user_id: int) -> Sticky:
    sticky = (
        db.query(Sticky)
        .options(selectinload(Sticky.tags))
        .filter(Sticky.id == sticky_id, Sticky.user_id == user_id)
        .first()
    )
    if sticky is None:
        raise HTTPException(status_code=404, detail="Sticky niet gevonden")
    return sticky


def _clean_color(color: str) -> str:
    return color if color in STICKY_COLORS else "yellow"


@router.get("")
def list_stickies(
    request: Request,
    tags: list[str] = Query(default=[]),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    _delete_expired_temp_stickies(db, user.id)
    query = db.query(Sticky).options(selectinload(Sticky.tags)).filter(Sticky.user_id == user.id)
    if tags:
        query = query.filter(Sticky.tags.any(Tag.name.in_(tags)))
    stickies = query.order_by(Sticky.updated_at.desc(), Sticky.id.desc()).all()
    all_tags = (
        db.query(Tag).join(Tag.stickies).filter(Sticky.user_id == user.id).distinct().order_by(Tag.name).all()
    )
    return templates.TemplateResponse(
        request,
        "stickies/list.html",
        {
            "user": user,
            "stickies": stickies,
            "all_tags": all_tags,
            "active_tags": tags,
            "colors": STICKY_COLOR_LABELS,
        },
    )


@router.post("")
def create_sticky(
    content: str = Form(""),
    color: str = Form("yellow"),
    tags: str = Form(""),
    is_temp: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sticky = Sticky(user_id=user.id, content=content, color=_clean_color(color), is_temp=is_temp)
    sticky.tags = resolve_tags(db, tags)
    db.add(sticky)
    db.commit()
    return RedirectResponse("/stickies", status_code=303)


@router.post("/{sticky_id}")
def update_sticky(
    sticky_id: int,
    request: Request,
    content: str = Form(""),
    color: str = Form("yellow"),
    tags: str = Form(""),
    is_temp: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sticky = _get_sticky_or_404(db, sticky_id, user.id)
    sticky.content = content
    sticky.color = _clean_color(color)
    sticky.is_temp = is_temp
    sticky.tags = resolve_tags(db, tags)
    db.commit()
    if request.headers.get("x-requested-with") == "fetch":  # auto-save vanuit stickies.js
        return Response(status_code=204)
    return RedirectResponse("/stickies", status_code=303)


@router.post("/{sticky_id}/delete")
def delete_sticky(sticky_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    db.delete(_get_sticky_or_404(db, sticky_id, user.id))
    db.commit()
    return RedirectResponse("/stickies", status_code=303)


