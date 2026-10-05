from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.tag import Tag
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/tasks", tags=["tasks"])

_SORT_OPTIONS = {
    "deadline": (Task.priority.desc(), Task.deadline.is_(None), Task.deadline, Task.created_at.desc()),
    "title": (Task.title.asc(),),
    "priority": (Task.priority.desc(), Task.title.asc()),
    "status": (Task.status.asc(), Task.title.asc()),
}
_GEEN_TAG_LABEL = "Zonder tag"
# Afgeronde taken verdwijnen na 24 uur uit de lijst (-> archief), en het archief wordt na
# 30 dagen leeggemaakt.
DONE_TASK_LIFETIME = timedelta(hours=24)
ARCHIVE_LIFETIME = timedelta(days=30)


def _apply_status(task: Task, new_status: TaskStatus) -> None:
    """Zet completed_at mee met de status i.p.v. dat als losse stap te laten doen door elke
    aanroeper -- zo kan dat nooit vergeten worden bij een van de twee plekken (het
    bewerkformulier en de snel-afvink-knop) die de status kunnen wijzigen."""
    if new_status == TaskStatus.DONE and task.status != TaskStatus.DONE:
        task.completed_at = datetime.now(UTC).replace(tzinfo=None)
    elif new_status != TaskStatus.DONE:
        task.completed_at = None
        task.archived_at = None
    task.status = new_status


def _archive_and_purge_tasks(db: Session, user_id: int) -> None:
    """Afgeronde taken gaan 24 uur na afronden naar het archief (archived_at), en
    gearchiveerde taken worden na 30 dagen definitief verwijderd -- zelfde "geen
    scheduler, opportunistisch bij elk bezoek"-patroon als tijdelijke notities (zie
    _delete_expired_temp_notes in app/routers/notes.py)."""
    now = datetime.now(UTC).replace(tzinfo=None)
    db.query(Task).filter(
        Task.user_id == user_id,
        Task.status == TaskStatus.DONE,
        Task.archived_at.is_(None),
        Task.completed_at.isnot(None),
        Task.completed_at < now - DONE_TASK_LIFETIME,
    ).update({Task.archived_at: now}, synchronize_session=False)
    db.query(Task).filter(
        Task.user_id == user_id,
        Task.archived_at.isnot(None),
        Task.archived_at < now - ARCHIVE_LIFETIME,
    ).delete(synchronize_session=False)
    db.commit()


def _redirect_to_list(
    sort: str = "deadline",
    group_by: str = "tag",
    tags: list[str] | None = None,
    status_filter: str | None = None,
) -> RedirectResponse:
    """Stuurt terug naar de takenlijst met dezelfde sortering/groepering/filters,
    zodat een snelle actie (afvinken, verwijderen) de huidige weergave niet reset."""
    params: dict[str, str | list[str]] = {"sort": sort, "group_by": group_by}
    if tags:
        params["tags"] = tags
    if status_filter:
        params["status_filter"] = status_filter
    return RedirectResponse(f"/tasks?{urlencode(params, doseq=True)}", status_code=303)


def _get_task_or_404(db: Session, task_id: int, user_id: int) -> Task:
    task = (
        db.query(Task)
        .options(selectinload(Task.tags))
        .filter(Task.id == task_id, Task.user_id == user_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Taak niet gevonden")
    return task


@router.get("")
def list_tasks(
    request: Request,
    tags: list[str] = Query(default=[]),
    status_filter: str | None = None,
    sort: str = "deadline",
    group_by: str = "tag",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sort = sort if sort in _SORT_OPTIONS else "deadline"
    _archive_and_purge_tasks(db, user.id)

    query = (
        db.query(Task)
        .options(selectinload(Task.tags))
        .filter(Task.user_id == user.id, Task.archived_at.is_(None))
    )
    if tags:
        query = query.filter(Task.tags.any(Tag.name.in_(tags)))
    if status_filter:
        query = query.filter(Task.status == status_filter)
    tasks = query.order_by(*_SORT_OPTIONS[sort]).all()

    all_tags = (
        db.query(Tag)
        .join(Tag.tasks)
        .filter(Task.user_id == user.id, Task.archived_at.is_(None))
        .distinct()
        .order_by(Tag.name)
        .all()
    )

    # Twee kolommen: dagtaken links, de rest rechts. Binnen elke kolom staan taken (bij
    # group_by=tag, de standaard) automatisch onder elkaar per tag -- onder de eerste tag
    # (alfabetisch) van de taak, zodat een taak met meerdere tags niet dubbel voorkomt.
    columns = []
    for key, title, column_tasks in (
        ("daily", "Dagtaken", [t for t in tasks if t.daily_task]),
        ("rest", "Overig", [t for t in tasks if not t.daily_task]),
    ):
        groups: list[tuple[str, list[Task]]] | None = None
        if group_by == "tag":
            by_tag: dict[str, list[Task]] = {}
            untagged: list[Task] = []
            for task in column_tasks:
                if task.tags:
                    by_tag.setdefault(min(t.name for t in task.tags), []).append(task)
                else:
                    untagged.append(task)
            groups = [(name, by_tag[name]) for name in sorted(by_tag)]
            if untagged:
                groups.append((_GEEN_TAG_LABEL, untagged))
        columns.append({"key": key, "title": title, "tasks": column_tasks, "groups": groups})

    return templates.TemplateResponse(
        request,
        "tasks/list.html",
        {
            "user": user,
            "tasks": tasks,
            "columns": columns,
            "statuses": list(TaskStatus),
            "all_tags": all_tags,
            "active_tags": tags,
            "active_status": status_filter,
            "sort": sort,
            "group_by": group_by,
        },
    )


@router.get("/archive")
def archived_tasks(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    _archive_and_purge_tasks(db, user.id)
    tasks = (
        db.query(Task)
        .options(selectinload(Task.tags))
        .filter(Task.user_id == user.id, Task.archived_at.isnot(None))
        .order_by(Task.archived_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "tasks/archive.html",
        {"user": user, "tasks": tasks, "archive_days": ARCHIVE_LIFETIME.days, "archive_lifetime": ARCHIVE_LIFETIME,
         "now_utc": datetime.now(UTC).replace(tzinfo=None)},
    )


@router.post("/{task_id}/restore")
def restore_task(task_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Haalt een gearchiveerde taak terug naar de takenlijst (status weer 'todo')."""
    task = _get_task_or_404(db, task_id, user.id)
    _apply_status(task, TaskStatus.TODO)
    db.commit()
    return RedirectResponse("/tasks/archive", status_code=303)


@router.get("/upcoming")
def upcoming_deadlines(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Kleine JSON-feed voor het deadline-widgetje in de sidebar (komende 5 deadlines)."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.deadline.isnot(None), Task.status != TaskStatus.DONE)
        .order_by(Task.deadline)
        .limit(5)
        .all()
    )
    return [
        {
            "id": t.id,
            "title": t.title,
            "deadline": t.deadline.isoformat(),
            "overdue": t.deadline_overdue,
            "warning": t.deadline_warning,
        }
        for t in tasks
    ]


@router.get("/ticker")
def ticker_tasks(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Kleine JSON-feed voor de nieuws-ticker onderin elke pagina (zie
    app/static/js/ticker.js) -- alleen nog niet afgeronde taken met "Prioriteit"
    aangevinkt (anders zou de band bij veel taken snel te druk/lang worden), op deadline
    gesorteerd (geen deadline achteraan)."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.status != TaskStatus.DONE, Task.priority.is_(True))
        .order_by(Task.deadline.is_(None), Task.deadline, Task.created_at.desc())
        .all()
    )
    return [{"id": t.id, "title": t.title, "priority": t.priority} for t in tasks]


@router.post("/quick")
def quick_create_task(
    title: str = Form(...),
    deadline: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Snel een taak aanmaken vanuit het mini-kalender-widgetje in de sidebar
    (klik op een dag) -- geeft JSON terug i.p.v. te redirecten, want de widget
    staat op elke pagina en mag de gebruiker niet wegnavigeren."""
    clean_title = title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Titel is verplicht")
    task = Task(
        user_id=user.id,
        title=clean_title,
        deadline=date.fromisoformat(deadline) if deadline else None,
    )
    db.add(task)
    db.commit()
    return {"id": task.id, "title": task.title, "deadline": deadline or None}


@router.get("/new")
def new_task_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "tasks/form.html", {"user": user, "task": None})


@router.post("")
def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(""),
    tags: str = Form(""),
    priority: bool = Form(False),
    daily_task: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = Task(
        user_id=user.id,
        title=title.strip(),
        description=description,
        deadline=date.fromisoformat(deadline) if deadline else None,
        priority=priority,
        daily_task=daily_task,
    )
    task.tags = resolve_tags(db, tags)
    db.add(task)
    db.commit()
    return RedirectResponse("/tasks", status_code=303)


@router.get("/{task_id}/edit")
def edit_task_form(task_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id, user.id)
    return templates.TemplateResponse(request, "tasks/form.html", {"user": user, "task": task})


@router.post("/{task_id}")
def update_task(
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(""),
    status_value: str = Form(...),
    tags: str = Form(""),
    priority: bool = Form(False),
    daily_task: bool = Form(False),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(db, task_id, user.id)
    task.title = title.strip()
    task.description = description
    task.deadline = date.fromisoformat(deadline) if deadline else None
    _apply_status(task, TaskStatus(status_value))
    task.priority = priority
    task.daily_task = daily_task
    task.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/tasks", status_code=303)


@router.post("/{task_id}/toggle-done")
def toggle_done(
    task_id: int,
    sort: str = Form("deadline"),
    group_by: str = Form("tag"),
    filter_tags: list[str] = Form(default=[]),
    status_filter: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Snel-afvink-knop: zet de taak op 'done', of terug naar 'todo' als 'm al klaar was."""
    task = _get_task_or_404(db, task_id, user.id)
    _apply_status(task, TaskStatus.TODO if task.status == TaskStatus.DONE else TaskStatus.DONE)
    db.commit()
    return _redirect_to_list(sort, group_by, filter_tags, status_filter or None)


@router.post("/{task_id}/delete")
def delete_task(
    task_id: int,
    sort: str = Form("deadline"),
    group_by: str = Form("tag"),
    filter_tags: list[str] = Form(default=[]),
    status_filter: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(db, task_id, user.id)
    db.delete(task)
    db.commit()
    return _redirect_to_list(sort, group_by, filter_tags, status_filter or None)
