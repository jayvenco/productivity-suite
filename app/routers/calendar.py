from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.calendar_event import CalendarEvent
from app.models.task import Task
from app.models.user import User
from app.services.calendar_grid import DUTCH_MONTHS, DUTCH_WEEKDAYS, add_months, month_weeks, week_dates
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _get_event_or_404(db: Session, event_id: int, user_id: int) -> CalendarEvent:
    event = (
        db.query(CalendarEvent)
        .options(selectinload(CalendarEvent.tags))
        .filter(CalendarEvent.id == event_id, CalendarEvent.user_id == user_id)
        .first()
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Afspraak niet gevonden")
    return event


def _items_by_date(
    days: list[date], user_id: int, db: Session
) -> tuple[dict[date, list[Task]], dict[date, list[CalendarEvent]]]:
    start, end = days[0], days[-1]
    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.deadline.isnot(None),
            Task.deadline >= start,
            Task.deadline <= end,
        )
        .all()
    )
    events = (
        db.query(CalendarEvent)
        .options(selectinload(CalendarEvent.tags))
        .filter(CalendarEvent.user_id == user_id, CalendarEvent.event_date >= start, CalendarEvent.event_date <= end)
        .all()
    )

    tasks_by_date: dict[date, list[Task]] = {}
    for task in tasks:
        tasks_by_date.setdefault(task.deadline, []).append(task)

    events_by_date: dict[date, list[CalendarEvent]] = {}
    for event in events:
        events_by_date.setdefault(event.event_date, []).append(event)

    return tasks_by_date, events_by_date


def _marked_dates(days: list[date], user_id: int, db: Session) -> set[date]:
    """Dagen binnen dit bereik die een taak-deadline of afspraak hebben --
    voor de rode stipjes in het mini-kalender-widgetje in de sidebar."""
    start, end = days[0], days[-1]
    task_dates = {
        row[0]
        for row in db.query(Task.deadline)
        .filter(Task.user_id == user_id, Task.deadline.isnot(None), Task.deadline >= start, Task.deadline <= end)
        .all()
    }
    event_dates = {
        row[0]
        for row in db.query(CalendarEvent.event_date)
        .filter(CalendarEvent.user_id == user_id, CalendarEvent.event_date >= start, CalendarEvent.event_date <= end)
        .all()
    }
    return task_dates | event_dates


@router.get("/widget")
def calendar_widget(
    year: int | None = None,
    month: int | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Kleine JSON-feed voor het mini-kalender-widgetje in de sidebar (zelfde
    opzet als /tasks/upcoming voor de deadlines-widget)."""
    today = date.today()
    year = year or today.year
    month = month or today.month
    weeks = month_weeks(year, month)
    days = [d for week in weeks for d in week]
    marked = _marked_dates(days, user.id, db)
    prev_year, prev_month = add_months(year, month, -1)
    next_year, next_month = add_months(year, month, 1)

    return {
        "label": f"{DUTCH_MONTHS[month - 1]} {year}",
        "day_labels": DUTCH_WEEKDAYS,
        "prev": {"year": prev_year, "month": prev_month},
        "next": {"year": next_year, "month": next_month},
        "weeks": [
            [
                {
                    "date": d.isoformat(),
                    "day": d.day,
                    "in_month": d.month == month,
                    "is_today": d == today,
                    "has_items": d in marked,
                }
                for d in week
            ]
            for week in weeks
        ],
    }


@router.get("")
def calendar_view(
    request: Request,
    view: str = "month",
    year: int | None = None,
    month: int | None = None,
    day: str | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    view = view if view in {"month", "week"} else "month"
    current_month: int | None = None

    if view == "week":
        reference = date.fromisoformat(day) if day else today
        days = week_dates(reference)
        weeks = [days]
        prev_url = f"/calendar?view=week&day={(days[0] - timedelta(days=7)).isoformat()}"
        next_url = f"/calendar?view=week&day={(days[0] + timedelta(days=7)).isoformat()}"
        title = f"Week van {days[0].day} {DUTCH_MONTHS[days[0].month - 1]} {days[0].year}"
    else:
        year = year or today.year
        month = month or today.month
        current_month = month
        weeks = month_weeks(year, month)
        days = [d for week in weeks for d in week]
        prev_year, prev_month = add_months(year, month, -1)
        next_year, next_month = add_months(year, month, 1)
        prev_url = f"/calendar?year={prev_year}&month={prev_month}"
        next_url = f"/calendar?year={next_year}&month={next_month}"
        title = f"{DUTCH_MONTHS[month - 1]} {year}"

    tasks_by_date, events_by_date = _items_by_date(days, user.id, db)

    return templates.TemplateResponse(
        request,
        "calendar/board.html",
        {
            "user": user,
            "view": view,
            "weeks": weeks,
            "title": title,
            "prev_url": prev_url,
            "next_url": next_url,
            "today": today,
            "current_month": current_month,
            "tasks_by_date": tasks_by_date,
            "events_by_date": events_by_date,
            "day_labels": DUTCH_WEEKDAYS,
        },
    )


@router.get("/events/new")
def new_event_form(request: Request, on: str | None = None, user: User = Depends(require_user)):
    return templates.TemplateResponse(
        request, "calendar/form.html", {"user": user, "event": None, "default_date": on or date.today().isoformat()}
    )


@router.post("/events")
def create_event(
    title: str = Form(...),
    event_date: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    parsed_date = date.fromisoformat(event_date)
    event = CalendarEvent(user_id=user.id, title=title.strip(), event_date=parsed_date, description=description)
    event.tags = resolve_tags(db, tags)
    db.add(event)
    db.commit()
    return RedirectResponse(f"/calendar?year={parsed_date.year}&month={parsed_date.month}", status_code=303)


@router.get("/events/{event_id}/edit")
def edit_event_form(
    event_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    event = _get_event_or_404(db, event_id, user.id)
    return templates.TemplateResponse(
        request, "calendar/form.html", {"user": user, "event": event, "default_date": None}
    )


@router.post("/events/{event_id}")
def update_event(
    event_id: int,
    title: str = Form(...),
    event_date: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    event = _get_event_or_404(db, event_id, user.id)
    parsed_date = date.fromisoformat(event_date)
    event.title = title.strip()
    event.event_date = parsed_date
    event.description = description
    event.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse(f"/calendar?year={parsed_date.year}&month={parsed_date.month}", status_code=303)


@router.post("/events/{event_id}/delete")
def delete_event(event_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    event = _get_event_or_404(db, event_id, user.id)
    year, month = event.event_date.year, event.event_date.month
    db.delete(event)
    db.commit()
    return RedirectResponse(f"/calendar?year={year}&month={month}", status_code=303)
