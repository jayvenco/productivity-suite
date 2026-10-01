from __future__ import annotations

import enum
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import task_tags
from app.services.tags import first_tag_hue_style


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_task: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    # Wanneer de taak voor het laatst op 'done' gezet is (None zolang dat nog niet zo is,
    # en weer teruggezet naar None als 'm terug naar todo/in_progress gaat) -- apart van
    # `updated_at`, dat bij élke wijziging meeverandert. Bepaalt wanneer een afgeronde taak
    # automatisch opgeruimd wordt (zie _delete_expired_done_tasks in app/routers/tasks.py).
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=task_tags, back_populates="tasks"
    )
    pomodoro_sessions: Mapped[list["PomodoroSession"]] = relationship(  # noqa: F821
        "PomodoroSession", back_populates="task"
    )

    @property
    def days_until_deadline(self) -> int | None:
        if self.deadline is None:
            return None
        return (self.deadline - date.today()).days

    @property
    def deadline_warning(self) -> bool:
        """True als de deadline binnen 3 dagen valt (en nog niet voorbij is)."""
        days = self.days_until_deadline
        return days is not None and 0 <= days <= 3

    @property
    def deadline_overdue(self) -> bool:
        days = self.days_until_deadline
        return days is not None and days < 0

    @property
    def stale(self) -> bool:
        """True als de taak meer dan 7 dagen niet meer bewerkt is (`updated_at`) --
        onafhankelijk van de deadline, puur "hier is al een tijdje niet meer naar
        omgekeken". `updated_at` is naive UTC (zie server_default=func.now()), dus
        vergelijken met een naive UTC "nu" i.p.v. lokale tijd."""
        return (datetime.now(UTC).replace(tzinfo=None) - self.updated_at).days > 7

    @property
    def completed_work_sessions(self) -> list["PomodoroSession"]:  # noqa: F821
        from app.models.pomodoro import PomodoroPhase, PomodoroStatus

        return [
            s
            for s in self.pomodoro_sessions
            if s.phase == PomodoroPhase.WORK and s.status == PomodoroStatus.COMPLETED
        ]

    @property
    def total_focus_minutes(self) -> int:
        return sum(s.planned_minutes for s in self.completed_work_sessions)

    @property
    def row_tint_style(self) -> str:
        """Zet --tag-hue op basis van de eerste tag (zie first_tag_hue_style) -- de
        standaard-thema's doen er niets mee, het "bubbles"-thema (themes/bubbles.css)
        gebruikt 'm voor een volle kleur op de taakkaart."""
        return first_tag_hue_style(self.tags)
