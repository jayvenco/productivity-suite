from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth.dependencies import get_current_user
from app.config import BASE_DIR, settings
from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.routers import account, auth, kanban, notes, pomodoro, settings as settings_router, snippets, tasks
from app.services.migrate import run_lightweight_migrations
from app.services.seed import seed_default_user_and_board
from app.services.tags import backfill_tag_colors

Base.metadata.create_all(bind=engine)
run_lightweight_migrations(engine)

with SessionLocal() as db:
    seed_default_user_and_board(db)
    backfill_tag_colors(db)

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(tasks.router)
app.include_router(kanban.router)
app.include_router(notes.router)
app.include_router(pomodoro.router)
app.include_router(snippets.router)
app.include_router(settings_router.router)


@app.get("/")
def home(request: Request, user: User | None = Depends(get_current_user)):
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/tasks", status_code=303)
