"""PWA-onderdelen (installeerbaar op Android/iOS): manifest, service worker en offline-pagina.
Deze routes zijn bewust publiek (geen login): de browser haalt ze zonder sessie op."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.config import BASE_DIR

router = APIRouter(tags=["pwa"])

_ICON_DIR = "/static/pwa"
_THEME = "#262a36"


def _manifest() -> dict:
    icon = lambda name, size, purpose="any": {  # noqa: E731
        "src": f"{_ICON_DIR}/{name}", "sizes": f"{size}x{size}", "type": "image/png", "purpose": purpose,
    }
    shortcut_icon = [{"src": f"{_ICON_DIR}/icon-192.png", "sizes": "192x192", "type": "image/png"}]
    return {
        "id": "/",
        "name": "Productivity Suite",
        "short_name": "Productiviteit",
        "description": "Taken, kanban, notities, inbox en scratchpad op je eigen server.",
        "lang": "nl",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": _THEME,
        "theme_color": _THEME,
        "icons": [
            icon("icon-192.png", 192),
            icon("icon-512.png", 512),
            icon("icon-maskable-512.png", 512, "maskable"),
        ],
        "shortcuts": [
            {"name": "Inbox", "url": "/inbox", "icons": shortcut_icon},
            {"name": "Scratchpad", "url": "/scratchpad", "icons": shortcut_icon},
            {"name": "Nieuwe taak", "url": "/tasks/new", "icons": shortcut_icon},
        ],
        # Android-deelmenu: tekst/link uit elke app delen naar de Inbox (zie /inbox/share).
        "share_target": {
            "action": "/inbox/share",
            "method": "POST",
            "enctype": "application/x-www-form-urlencoded",
            "params": {"title": "title", "text": "text", "url": "url"},
        },
    }


@router.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(_manifest(), media_type="application/manifest+json")


@router.get("/service-worker.js")
def service_worker():
    return FileResponse(
        BASE_DIR / "app" / "static" / "pwa" / "service-worker.js",
        media_type="application/javascript",
        # no-cache: een nieuwe versie van de service worker moet meteen opgepikt worden
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


_OFFLINE_HTML = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#262a36"><title>Offline - Productivity Suite</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#262a36;
       color:#e6e6ea;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;text-align:center;padding:24px}
  h1{font-size:22px;margin:0 0 8px} p{color:#9a9aa3;margin:0 0 20px;max-width:320px}
  button{background:#ef8354;color:#fff;border:none;border-radius:10px;padding:10px 20px;font-size:15px;cursor:pointer}
</style></head><body><div>
<h1>Je bent offline</h1>
<p>De server is nu niet bereikbaar. Controleer je wifi of VPN en probeer het opnieuw.</p>
<button onclick="location.reload()">Opnieuw proberen</button>
</div></body></html>"""


@router.get("/offline", response_class=HTMLResponse)
def offline_page():
    return HTMLResponse(_OFFLINE_HTML)
