from __future__ import annotations

import markdown as md
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.services.checklist import render_description_html

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def render_markdown(text: str) -> str:
    """Basis tekstverwerking: vet, cursief, lijsten, headers, links, code-blokken."""
    if not text:
        return ""
    return md.markdown(text, extensions=["extra", "nl2br"])


def render_card_description(description: str, card_id: int) -> str:
    return render_description_html(description, card_id, render_markdown)


templates.env.filters["markdown"] = render_markdown
templates.env.filters["checklist_html"] = render_card_description
