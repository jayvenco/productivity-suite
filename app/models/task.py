from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.tag import task_tags


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
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

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

    URGENCY_WINDOW_DAYS = 14
    _URGENCY_START_RGB = (63, 63, 70)  # antraciet
    _URGENCY_END_RGB = (154, 52, 18)  # donkeroranje

    @property
    def urgency_color(self) -> str | None:
        """Kleur voor de dunne deadline-balk: antraciet ver van de deadline, geleidelijk
        naar donkeroranje naarmate de deadline nadert (en blijft donkeroranje als de
        deadline al verstreken is)."""
        days = self.days_until_deadline
        if days is None:
            return None

        fraction = max(0.0, min(1.0, (self.URGENCY_WINDOW_DAYS - days) / self.URGENCY_WINDOW_DAYS))
        r = round(self._URGENCY_START_RGB[0] + (self._URGENCY_END_RGB[0] - self._URGENCY_START_RGB[0]) * fraction)
        g = round(self._URGENCY_START_RGB[1] + (self._URGENCY_END_RGB[1] - self._URGENCY_START_RGB[1]) * fraction)
        b = round(self._URGENCY_START_RGB[2] + (self._URGENCY_END_RGB[2] - self._URGENCY_START_RGB[2]) * fraction)
        return f"rgb({r}, {g}, {b})"

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
