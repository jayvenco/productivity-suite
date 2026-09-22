from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.kanban import KanbanBoard, KanbanCard
from app.models.note import Note
from app.models.pomodoro import PomodoroPhase, PomodoroSession, PomodoroStatus
from app.models.task import Task, TaskStatus

DAY_CHART_LENGTH = 14
WEEK_CHART_LENGTH = 8
MONTH_CHART_LENGTH = 6


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


def _last_n_days(n: int, today: date) -> list[date]:
    return [today - timedelta(days=offset) for offset in range(n - 1, -1, -1)]


def _last_n_week_starts(n: int, today: date) -> list[date]:
    this_week_start = today - timedelta(days=today.weekday())
    return [this_week_start - timedelta(weeks=offset) for offset in range(n - 1, -1, -1)]


def _last_n_months(n: int, today: date) -> list[tuple[int, int]]:
    months = []
    year, month = today.year, today.month
    for _ in range(n):
        months.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))


def _bars(buckets: dict, keys: list, *, label_fn) -> list[dict]:
    """Zet een {key: aantal}-mapping om naar een lijst chart-punten met een
    percentage t.o.v. de hoogste waarde in de reeks -- zodat de template puur
    op basis van `pct` de balkhoogte kan zetten, zonder zelf te hoeven rekenen."""
    values = [buckets[key] for key in keys]
    max_value = max(values) if values else 0
    return [
        {"label": label_fn(key), "value": buckets[key], "pct": round((buckets[key] / max_value) * 100) if max_value else 0}
        for key in keys
    ]


def _grouped_bars(created: dict, done: dict, keys: list, *, label_fn) -> list[dict]:
    max_value = max([*created.values(), *done.values()]) if keys else 0
    points = []
    for key in keys:
        c, d = created[key], done[key]
        points.append(
            {
                "label": label_fn(key),
                "created": c,
                "done": d,
                "created_pct": round((c / max_value) * 100) if max_value else 0,
                "done_pct": round((d / max_value) * 100) if max_value else 0,
            }
        )
    return points


def compute_activity_charts(db: Session, user_id: int) -> dict:
    """Grafiekdata voor de statistiekenpagina: focustijd en aangemaakte/afgeronde
    items per dag/week/maand. Bewust in Python gebucket (i.p.v. SQL GROUP BY per
    databasedialect) -- bij een persoonlijke app is het datavolume klein genoeg
    en blijft de logica zo makkelijk leesbaar en te testen."""
    today = date.today()
    days = _last_n_days(DAY_CHART_LENGTH, today)
    week_starts = _last_n_week_starts(WEEK_CHART_LENGTH, today)
    months = _last_n_months(MONTH_CHART_LENGTH, today)
    range_start = datetime.combine(date(months[0][0], months[0][1], 1), time.min)

    created_timestamps: list[datetime] = []
    for ts, in db.query(Task.created_at).filter(Task.user_id == user_id, Task.created_at >= range_start):
        created_timestamps.append(ts)
    for ts, in db.query(Note.created_at).filter(Note.user_id == user_id, Note.created_at >= range_start):
        created_timestamps.append(ts)
    card_created = (
        db.query(KanbanCard.created_at)
        .join(KanbanBoard, KanbanCard.board_id == KanbanBoard.id)
        .filter(KanbanBoard.user_id == user_id, KanbanCard.created_at >= range_start)
    )
    for ts, in card_created:
        created_timestamps.append(ts)

    done_timestamps = [
        ts
        for ts, in db.query(Task.updated_at).filter(
            Task.user_id == user_id, Task.status == TaskStatus.DONE, Task.updated_at >= range_start
        )
    ]

    focus_rows = db.query(PomodoroSession.started_at, PomodoroSession.planned_minutes).filter(
        PomodoroSession.user_id == user_id,
        PomodoroSession.phase == PomodoroPhase.WORK,
        PomodoroSession.status == PomodoroStatus.COMPLETED,
        PomodoroSession.started_at >= range_start,
    )

    def _week_start_of(d: date) -> date:
        return d - timedelta(days=d.weekday())

    created_by_day = {d: 0 for d in days}
    created_by_week = {w: 0 for w in week_starts}
    created_by_month = {m: 0 for m in months}
    for ts in created_timestamps:
        d = ts.date()
        if d in created_by_day:
            created_by_day[d] += 1
        w = _week_start_of(d)
        if w in created_by_week:
            created_by_week[w] += 1
        ym = (ts.year, ts.month)
        if ym in created_by_month:
            created_by_month[ym] += 1

    done_by_day = {d: 0 for d in days}
    done_by_week = {w: 0 for w in week_starts}
    done_by_month = {m: 0 for m in months}
    for ts in done_timestamps:
        d = ts.date()
        if d in done_by_day:
            done_by_day[d] += 1
        w = _week_start_of(d)
        if w in done_by_week:
            done_by_week[w] += 1
        ym = (ts.year, ts.month)
        if ym in done_by_month:
            done_by_month[ym] += 1

    focus_by_day = {d: 0 for d in days}
    focus_by_month = {m: 0 for m in months}
    for started_at, minutes in focus_rows:
        d = started_at.date()
        if d in focus_by_day:
            focus_by_day[d] += minutes
        ym = (started_at.year, started_at.month)
        if ym in focus_by_month:
            focus_by_month[ym] += minutes

    days_elapsed_this_month = today.day
    focus_avg_per_day_this_month = round(focus_by_month[(today.year, today.month)] / days_elapsed_this_month, 1)

    return {
        "focus_by_day": _bars(focus_by_day, days, label_fn=lambda d: d.strftime("%d/%m")),
        "focus_by_month": _bars(focus_by_month, months, label_fn=lambda ym: date(ym[0], ym[1], 1).strftime("%b")),
        "focus_avg_per_day_this_month": focus_avg_per_day_this_month,
        "items_by_day": _grouped_bars(created_by_day, done_by_day, days, label_fn=lambda d: d.strftime("%d/%m")),
        "items_by_week": _grouped_bars(
            created_by_week, done_by_week, week_starts, label_fn=lambda w: w.strftime("%d/%m")
        ),
        "items_by_month": _grouped_bars(
            created_by_month, done_by_month, months, label_fn=lambda ym: date(ym[0], ym[1], 1).strftime("%b")
        ),
    }
