from __future__ import annotations

import os
from datetime import UTC, datetime

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


def relative_time(dt: datetime | None) -> str:
    """Relatieve tijdsaanduiding (bv. "3 dagen geleden") i.p.v. een kale datum -- gebruikt
    op de ByteStash-achtige snippet-kaarten (zie app/templates/snippets/list.html), die
    de laatste-wijziging-tijd prominent rechtsboven in de kaart tonen."""
    if dt is None:
        return ""
    delta = datetime.now(UTC).replace(tzinfo=None) - dt
    seconds = delta.total_seconds()
    if seconds < 60:
        return "zojuist"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} min. geleden"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} uur geleden"
    days = delta.days
    if days < 1:
        return "vandaag"
    if days == 1:
        return "1 dag geleden"
    if days < 30:
        return f"{days} dagen geleden"
    months = days // 30
    if months < 12:
        return f"ongeveer {months} maand{'en' if months != 1 else ''} geleden"
    years = days // 365
    return f"ongeveer {years} jaar{'en' if years != 1 else ''} geleden"


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
templates.env.filters["relative_time"] = relative_time
templates.env.globals["static_url"] = static_url
