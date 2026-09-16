from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.config import settings
from app.database import get_db
from app.models.pomodoro import PomodoroPhase, PomodoroSession, PomodoroStatus
from app.models.task import Task, TaskStatus
from app.models.user import User

router = APIRouter(prefix="/pomodoro", tags=["pomodoro"])


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _serialize(session: PomodoroSession) -> dict:
    return {
        "id": session.id,
        "phase": session.phase.value,
        "status": session.status.value,
        "planned_minutes": session.planned_minutes,
        "started_at": session.started_at.isoformat(),
        "task_id": session.task_id,
        "task_title": session.task.title if session.task else None,
    }


@router.get("/state")
def get_state(user: User = Depends(require_user), db: Session = Depends(get_db)):
    active = (
        db.query(PomodoroSession)
        .filter(PomodoroSession.user_id == user.id, PomodoroSession.status == PomodoroStatus.RUNNING)
        .order_by(PomodoroSession.started_at.desc())
        .first()
    )
    return {
        "active": _serialize(active) if active else None,
        "default_work_minutes": settings.pomodoro_work_minutes,
        "default_break_minutes": settings.pomodoro_break_minutes,
    }


@router.get("/tasks")
def list_open_tasks(user: User = Depends(require_user), db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.status != TaskStatus.DONE)
        .order_by(Task.title)
        .all()
    )
    return [{"id": t.id, "title": t.title} for t in tasks]


@router.post("/start")
def start_session(
    phase: str = Form(...),
    minutes: int = Form(...),
    task_id: int | None = Form(None),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    try:
        phase_enum = PomodoroPhase(phase)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ongeldige fase") from exc
    if minutes <= 0:
        raise HTTPException(status_code=400, detail="Duur moet positief zijn")

    if task_id is not None:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
        if task is None:
            raise HTTPException(status_code=404, detail="Taak niet gevonden")

    # Er kan maar één timer tegelijk lopen: eerdere lopende sessies afbreken.
    db.query(PomodoroSession).filter(
        PomodoroSession.user_id == user.id, PomodoroSession.status == PomodoroStatus.RUNNING
    ).update({"status": PomodoroStatus.CANCELLED, "ended_at": _utcnow()})

    session = PomodoroSession(
        user_id=user.id,
        task_id=task_id,
        phase=phase_enum,
        status=PomodoroStatus.RUNNING,
        planned_minutes=minutes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize(session)


@router.post("/{session_id}/finish")
def finish_session(session_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    session = db.get(PomodoroSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.status = PomodoroStatus.COMPLETED
    session.ended_at = _utcnow()
    db.commit()
    return {"ok": True}


@router.post("/{session_id}/cancel")
def cancel_session(session_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    session = db.get(PomodoroSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Sessie niet gevonden")
    session.status = PomodoroStatus.CANCELLED
    session.ended_at = _utcnow()
    db.commit()
    return {"ok": True}
