from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])

AVAILABLE_THEMES = ["dracula", "one-dark-pro", "nord", "light", "nexmail"]

# (id, label). id is ook de data-font-waarde die app.css afvangt met
# [data-font="..."] om --font-sans/--font-heading te zetten.
AVAILABLE_FONTS = [
    ("system", "Systeemstandaard"),
    ("inter", "Inter"),
    ("roboto", "Roboto"),
    ("open-sans", "Open Sans"),
    ("lato", "Lato"),
    ("poppins", "Poppins"),
    ("nunito", "Nunito"),
    ("source-sans", "Source Sans 3"),
    ("merriweather", "Merriweather"),
    ("fira-sans", "Fira Sans"),
    ("hack", "Hack (monospace)"),
    ("jetbrains-mono", "JetBrains Mono (monospace)"),
    ("fira-code", "Fira Code (monospace)"),
    ("consolas", "Consolas (monospace, alleen als lokaal geïnstalleerd)"),
]
AVAILABLE_FONT_IDS = {font_id for font_id, _ in AVAILABLE_FONTS}

AVAILABLE_FONT_SIZES = [13, 14, 15, 16, 17, 18]

AVAILABLE_DENSITIES = [
    ("comfortable", "Comfortabel"),
    ("compact", "Compact"),
]


@router.post("/theme")
def set_theme(
    theme: str = Form(...),
    redirect_to: str = Form("/"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if theme in AVAILABLE_THEMES:
        user.theme = theme
        db.commit()
    return RedirectResponse(redirect_to, status_code=303)


@router.post("/appearance")
def set_appearance(
    font_family: str = Form(...),
    font_size: int = Form(...),
    density: str = Form(...),
    redirect_to: str = Form("/account"),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if font_family in AVAILABLE_FONT_IDS:
        user.font_family = font_family
    if font_size in AVAILABLE_FONT_SIZES:
        user.font_size = font_size
    if density in {density_id for density_id, _ in AVAILABLE_DENSITIES}:
        user.density = density
    db.commit()
    return RedirectResponse(redirect_to, status_code=303)
