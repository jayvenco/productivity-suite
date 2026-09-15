from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/tasks", tags=["tasks"])


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
    tag: str | None = None,
    status_filter: str | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = db.query(Task).options(selectinload(Task.tags)).filter(Task.user_id == user.id)
    if tag:
        query = query.filter(Task.tags.any(name=tag))
    if status_filter:
        query = query.filter(Task.status == status_filter)
    tasks = query.order_by(Task.deadline.is_(None), Task.deadline, Task.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "tasks/list.html",
        {"user": user, "tasks": tasks, "statuses": list(TaskStatus), "active_tag": tag},
    )


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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = Task(
        user_id=user.id,
        title=title.strip(),
        description=description,
        deadline=date.fromisoformat(deadline) if deadline else None,
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
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    task = _get_task_or_404(db, task_id, user.id)
    task.title = title.strip()
    task.description = description
    task.deadline = date.fromisoformat(deadline) if deadline else None
    task.status = TaskStatus(status_value)
    task.tags = resolve_tags(db, tags)
    db.commit()
    return RedirectResponse("/tasks", status_code=303)


@router.post("/{task_id}/delete")
def delete_task(task_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id, user.id)
    db.delete(task)
    db.commit()
    return RedirectResponse("/tasks", status_code=303)
