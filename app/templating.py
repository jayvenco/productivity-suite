from __future__ import annotations

import markdown as md
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


def render_markdown(text: str) -> str:
    """Basis tekstverwerking: vet, cursief, lijsten, headers, links, code-blokken."""
    if not text:
        return ""
    return md.markdown(text, extensions=["extra", "nl2br"])


templates.env.filters["markdown"] = render_markdown
