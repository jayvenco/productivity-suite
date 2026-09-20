from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.kanban import KanbanBoard, KanbanCard
from app.models.note import Note
from app.models.pomodoro import PomodoroPhase, PomodoroSession, PomodoroStatus
from app.models.task import Task, TaskStatus


def _week_start(today: date) -> datetime:
    return datetime.combine(today - timedelta(days=today.weekday()), time.min)


def _month_start(today: date) -> datetime:
    return datetime.combine(today.replace(day=1), time.min)


def compute_user_stats(db: Session, user_id: int) -> dict:
    """Simpele productiviteitsstatistieken voor de accountpagina. Bewust
    query-based (geen Python-side property-loops zoals Task.deadline_overdue)
    zodat dit ook bij veel taken/kaarten/notities snel blijft."""
    today = date.today()
    week_start = _week_start(today)
    month_start = _month_start(today)

    total_tasks = db.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar() or 0
    done_tasks = (
        db.query(func.count(Task.id)).filter(Task.user_id == user_id, Task.status == TaskStatus.DONE).scalar() or 0
    )
    completion_rate = round((done_tasks / total_tasks) * 100) if total_tasks else 0

    high_priority_open = (
        db.query(func.count(Task.id))
        .filter(Task.user_id == user_id, Task.priority.is_(True), Task.status != TaskStatus.DONE)
        .scalar()
        or 0
    )

    # "Behaalde deadline" = afgeronde taak met een deadline, klaargezet vóór of op
    # die deadline. Er is geen apart "voltooid op"-veld, dus updated_at (dat
    # bijwerkt bij elke wijziging, inclusief het afvinken) is de beste proxy.
    deadlines_met = (
        db.query(func.count(Task.id))
        .filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.DONE,
            Task.deadline.isnot(None),
            func.date(Task.updated_at) <= Task.deadline,
        )
        .scalar()
        or 0
    )
    deadlines_overdue_open = (
        db.query(func.count(Task.id))
        .filter(Task.user_id == user_id, Task.status != TaskStatus.DONE, Task.deadline.isnot(None), Task.deadline < today)
        .scalar()
        or 0
    )
    tasks_created_this_week = (
        db.query(func.count(Task.id)).filter(Task.user_id == user_id, Task.created_at >= week_start).scalar() or 0
    )
    tasks_created_this_month = (
        db.query(func.count(Task.id)).filter(Task.user_id == user_id, Task.created_at >= month_start).scalar() or 0
    )

    total_notes = db.query(func.count(Note.id)).filter(Note.user_id == user_id).scalar() or 0
    notes_created_this_week = (
        db.query(func.count(Note.id)).filter(Note.user_id == user_id, Note.created_at >= week_start).scalar() or 0
    )
    notes_created_this_month = (
        db.query(func.count(Note.id)).filter(Note.user_id == user_id, Note.created_at >= month_start).scalar() or 0
    )

    card_query = db.query(func.count(KanbanCard.id)).join(
        KanbanBoard, KanbanCard.board_id == KanbanBoard.id
    ).filter(KanbanBoard.user_id == user_id)
    total_cards = card_query.scalar() or 0
    cards_created_this_week = card_query.filter(KanbanCard.created_at >= week_start).scalar() or 0
    cards_created_this_month = card_query.filter(KanbanCard.created_at >= month_start).scalar() or 0

    work_sessions = db.query(PomodoroSession).filter(
        PomodoroSession.user_id == user_id, PomodoroSession.phase == PomodoroPhase.WORK
    )
    sessions_started = work_sessions.count()
    completed_sessions = work_sessions.filter(PomodoroSession.status == PomodoroStatus.COMPLETED)
    sessions_completed = completed_sessions.count()
    focus_minutes_total = (
        db.query(func.coalesce(func.sum(PomodoroSession.planned_minutes), 0))
        .filter(
            PomodoroSession.user_id == user_id,
            PomodoroSession.phase == PomodoroPhase.WORK,
            PomodoroSession.status == PomodoroStatus.COMPLETED,
        )
        .scalar()
        or 0
    )
    focus_minutes_this_week = (
        db.query(func.coalesce(func.sum(PomodoroSession.planned_minutes), 0))
        .filter(
            PomodoroSession.user_id == user_id,
            PomodoroSession.phase == PomodoroPhase.WORK,
            PomodoroSession.status == PomodoroStatus.COMPLETED,
            PomodoroSession.started_at >= week_start,
        )
        .scalar()
        or 0
    )

    return {
        "tasks": {
            "total": total_tasks,
            "done": done_tasks,
            "completion_rate": completion_rate,
            "high_priority_open": high_priority_open,
            "deadlines_met": deadlines_met,
            "deadlines_overdue_open": deadlines_overdue_open,
            "created_this_week": tasks_created_this_week,
            "created_this_month": tasks_created_this_month,
        },
        "notes": {
            "total": total_notes,
            "created_this_week": notes_created_this_week,
            "created_this_month": notes_created_this_month,
        },
        "kanban": {
            "total": total_cards,
            "created_this_week": cards_created_this_week,
            "created_this_month": cards_created_this_month,
        },
        "pomodoro": {
            "sessions_started": sessions_started,
            "sessions_completed": sessions_completed,
            "focus_minutes_total": focus_minutes_total,
            "focus_minutes_this_week": focus_minutes_this_week,
        },
    }
