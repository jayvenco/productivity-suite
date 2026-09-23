from __future__ import annotations

import os

import bleach
import markdown as md
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.services.checklist import render_description_html

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

_STATIC_DIR = BASE_DIR / "app" / "static"


def render_markdown(text: str) -> str:
    """Basis tekstverwerking: vet, cursief, lijsten, headers, links, code-blokken.
    Kale URL's (met of zonder www./schema) die niet als `[tekst](url)` zijn
    getypt, worden na de markdown-conversie alsnog automatisch aanklikbaar
    gemaakt -- code-blokken/inline code blijven bewust platte tekst."""
    if not text:
        return ""
    html = md.markdown(text, extensions=["extra", "nl2br"])
    return bleach.linkify(html, parse_email=False, skip_tags=["code", "pre"])


def render_card_description(description: str, card_id: int) -> str:
    return render_description_html(description, card_id, render_markdown)


def static_url(path: str) -> str:
    """Statische bestanden (CSS/JS) krijgen een ?v=<mtime>-querystring, zodat
    een gewijzigd bestand na een deploy altijd een nieuwe URL heeft i.p.v. dat
    browsers een oude, gecachte versie blijven tonen totdat iemand handmatig
    de cache leegt -- dat leidde er eerder toe dat een bijgewerkte app.css/
    pomodoro.js pas zichtbaar werd na een harde refresh."""
    try:
        version = int(os.path.getmtime(_STATIC_DIR / path))
    except OSError:
        version = 0
    return f"/static/{path}?v={version}"


templates.env.filters["markdown"] = render_markdown
templates.env.filters["checklist_html"] = render_card_description
templates.env.globals["static_url"] = static_url
