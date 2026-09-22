from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.user import User
from app.services.stats import compute_activity_charts, compute_user_stats
from app.templating import templates

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def stats_view(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "stats/view.html",
        {
            "user": user,
            "stats": compute_user_stats(db, user.id),
            "charts": compute_activity_charts(db, user.id),
        },
    )
