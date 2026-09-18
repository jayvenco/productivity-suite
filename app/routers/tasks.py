from __future__ import annotations

from datetime import date
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


def _redirect_to_list(
    sort: str = "deadline",
    group_by: str = "none",
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
    group_by: str = "none",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    sort = sort if sort in _SORT_OPTIONS else "deadline"

    query = db.query(Task).options(selectinload(Task.tags)).filter(Task.user_id == user.id)
    if tags:
        query = query.filter(Task.tags.any(Tag.name.in_(tags)))
    if status_filter:
        query = query.filter(Task.status == status_filter)
    tasks = query.order_by(*_SORT_OPTIONS[sort]).all()

    all_tags = (
        db.query(Tag)
        .join(Tag.tasks)
        .filter(Task.user_id == user.id)
        .distinct()
        .order_by(Tag.name)
        .all()
    )

    groups: list[tuple[str, list[Task]]] | None = None
    if group_by == "tag":
        by_tag: dict[str, list[Task]] = {}
        untagged: list[Task] = []
        for task in tasks:
            if not task.tags:
                untagged.append(task)
            for t in task.tags:
                by_tag.setdefault(t.name, []).append(task)
        groups = [(name, by_tag[name]) for name in sorted(by_tag)]
        if untagged:
            groups.append((_GEEN_TAG_LABEL, untagged))

    return templates.TemplateResponse(
        request,
        "tasks/list.html",
        {
            "user": user,
            "tasks": tasks,
            "groups": groups,
            "statuses": list(TaskStatus),
            "all_tags": all_tags,
            "active_tags": tags,
            "active_status": status_filter,
            "sort": sort,
            "group_by": group_by,
        },
    )


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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = Task(
        user_id=user.id,
        title=title.strip(),
        description=description,
        deadline=date.fromisoformat(deadline) if deadline else None,
        priority=priority,
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(db, task_id, user.id)
    task.title = title.strip()
    task.description = description
    task.deadline = date.fromisoformat(deadline) if deadline else None
    task.status = TaskStatus(status_value)
    task.priority = priority
    task.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/tasks", status_code=303)


@router.post("/{task_id}/toggle-done")
def toggle_done(
    task_id: int,
    sort: str = Form("deadline"),
    group_by: str = Form("none"),
    filter_tags: list[str] = Form(default=[]),
    status_filter: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Snel-afvink-knop: zet de taak op 'done', of terug naar 'todo' als 'm al klaar was."""
    task = _get_task_or_404(db, task_id, user.id)
    task.status = TaskStatus.TODO if task.status == TaskStatus.DONE else TaskStatus.DONE
    db.commit()
    return _redirect_to_list(sort, group_by, filter_tags, status_filter or None)


@router.post("/{task_id}/delete")
def delete_task(
    task_id: int,
    sort: str = Form("deadline"),
    group_by: str = Form("none"),
    filter_tags: list[str] = Form(default=[]),
    status_filter: str = Form(""),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(db, task_id, user.id)
    db.delete(task)
    db.commit()
    return _redirect_to_list(sort, group_by, filter_tags, status_filter or None)
