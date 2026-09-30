from __future__ import annotations

import json
from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import require_user
from app.database import get_db
from app.models.snippet import Snippet, SnippetFile
from app.models.tag import Tag
from app.models.user import User
from app.services.tags import resolve_tags
from app.templating import templates

router = APIRouter(prefix="/snippets", tags=["snippets"])


def _get_snippet_or_404(db: Session, snippet_id: int, user_id: int) -> Snippet:
    snippet = (
        db.query(Snippet)
        .options(selectinload(Snippet.tags), selectinload(Snippet.files))
        .filter(Snippet.id == snippet_id, Snippet.user_id == user_id)
        .first()
    )
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet niet gevonden")
    return snippet


def _apply_files_from_form(db: Session, snippet: Snippet, form) -> None:
    filenames = form.getlist("filename")
    languages = form.getlist("language")
    contents = form.getlist("content")

    snippet.files.clear()
    db.flush()

    position = 0
    for filename, language, content in zip(filenames, languages, contents):
        if not filename.strip() and not content.strip():
            continue
        db.add(
            SnippetFile(
                snippet_id=snippet.id,
                filename=filename.strip() or f"bestand{position + 1}",
                language=(language or "plaintext").strip() or "plaintext",
                content=content,
                position=position,
            )
        )
        position += 1


@router.get("")
def list_snippets(
    request: Request,
    q: str | None = None,
    tag: str | None = None,
    import_error: str | None = None,
    import_success: str | None = None,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Snippet)
        .options(selectinload(Snippet.tags), selectinload(Snippet.files))
        .filter(Snippet.user_id == user.id)
    )
    if tag:
        query = query.filter(Snippet.tags.any(name=tag))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Snippet.title.ilike(like),
                Snippet.tags.any(Tag.name.ilike(like)),
                Snippet.files.any(SnippetFile.content.ilike(like)),
            )
        )

    snippets = query.order_by(Snippet.updated_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "snippets/list.html",
        {
            "user": user,
            "snippets": snippets,
            "active_tag": tag,
            "q": q or "",
            "import_error": import_error,
            "import_success": import_success,
        },
    )


@router.get("/new")
def new_snippet_form(request: Request, user: User = Depends(require_user)):
    return templates.TemplateResponse(request, "snippets/form.html", {"user": user, "snippet": None})


@router.post("")
async def create_snippet(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    form = await request.form()
    title = (form.get("title") or "").strip()

    snippet = Snippet(user_id=user.id, title=title, description=form.get("description") or "")
    snippet.tags = resolve_tags(db, form.get("tags") or "")
    db.add(snippet)
    db.flush()
    _apply_files_from_form(db, snippet, form)
    db.commit()
    return RedirectResponse("/snippets", status_code=303)


@router.post("/bulk-delete")
async def bulk_delete_snippets(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    # Moet vóór de generieke /{snippet_id}-routes staan, anders matcht FastAPI
    # "bulk-delete" per ongeluk als snippet_id (en geeft dan een 422 i.p.v. dit uit te
    # voeren) -- zelfde volgorde-eis als bij de /bulk-delete-route in app/routers/notes.py.
    form = await request.form()
    snippet_ids = [int(v) for v in form.getlist("snippet_ids")]
    if snippet_ids:
        db.query(Snippet).filter(Snippet.id.in_(snippet_ids), Snippet.user_id == user.id).delete(
            synchronize_session=False
        )
        db.commit()

    params: dict[str, str] = {}
    if form.get("q"):
        params["q"] = form.get("q")
    if form.get("tag"):
        params["tag"] = form.get("tag")
    query = f"?{urlencode(params)}" if params else ""
    return RedirectResponse(f"/snippets{query}", status_code=303)


@router.get("/export")
def export_snippets(
    format: str = "json", user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """Exporteert alle snippets van de gebruiker als downloadbaar bestand -- bewust een
    los, snippet-only exportformaat i.p.v. de hele-database-backup (Account -> Backup):
    dit is bedoeld om te delen/lezen (JSON is ook weer te importeren, zie hieronder;
    markdown is puur leesbaar/deelbaar, geen id's/interne structuur). Geen database-id's
    in de export, zodat een import op een andere installatie geen conflicten geeft."""
    snippets = (
        db.query(Snippet)
        .options(selectinload(Snippet.tags), selectinload(Snippet.files))
        .filter(Snippet.user_id == user.id)
        .order_by(Snippet.title)
        .all()
    )
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

    if format == "markdown":
        lines = ["# Snippets-export", ""]
        for snippet in snippets:
            lines.append(f"## {snippet.title}")
            if snippet.description:
                lines.append(snippet.description)
            if snippet.tags:
                lines.append(f"Tags: {', '.join(t.name for t in snippet.tags)}")
            lines.append("")
            for file in snippet.files:
                lines.append(f"### {file.filename}")
                lines.append(f"```{file.language}")
                lines.append(file.content)
                lines.append("```")
                lines.append("")
            lines.append("---")
            lines.append("")
        body = "\n".join(lines)
        return Response(
            body,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="snippets-export-{timestamp}.md"'},
        )

    payload = {
        "exported_at": datetime.now(UTC).isoformat(),
        "snippets": [
            {
                "title": s.title,
                "description": s.description,
                "tags": [t.name for t in s.tags],
                "files": [
                    {"filename": f.filename, "language": f.language, "content": f.content} for f in s.files
                ],
            }
            for s in snippets
        ],
    }
    return Response(
        json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="snippets-export-{timestamp}.json"'},
    )


@router.post("/import")
async def import_snippets(
    import_file: UploadFile = File(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Importeert snippets uit een eerder geëxporteerd JSON-bestand (zie export_snippets
    hierboven) -- voegt toe aan de bestaande snippets i.p.v. te overschrijven, want dit is
    een gerichte snippet-import, geen volledige database-restore zoals Account -> Backup."""
    raw = await import_file.read()
    try:
        payload = json.loads(raw)
        entries = payload["snippets"]
        if not isinstance(entries, list):
            raise ValueError("'snippets' moet een lijst zijn")
    except (json.JSONDecodeError, KeyError, ValueError, UnicodeDecodeError):
        error = urlencode({"import_error": "Ongeldig of beschadigd JSON-bestand"})
        return RedirectResponse(f"/snippets?{error}", status_code=303)

    imported = 0
    for entry in entries:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        snippet = Snippet(user_id=user.id, title=title, description=(entry.get("description") or "").strip())
        snippet.tags = resolve_tags(db, ", ".join(entry.get("tags") or []))
        db.add(snippet)
        db.flush()
        for position, file_entry in enumerate(entry.get("files") or []):
            db.add(
                SnippetFile(
                    snippet_id=snippet.id,
                    filename=(file_entry.get("filename") or f"bestand{position + 1}").strip(),
                    language=(file_entry.get("language") or "plaintext").strip() or "plaintext",
                    content=file_entry.get("content") or "",
                    position=position,
                )
            )
        imported += 1
    db.commit()

    return RedirectResponse(f"/snippets?import_success={imported}", status_code=303)


@router.get("/{snippet_id}/edit")
def edit_snippet_form(
    snippet_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    snippet = _get_snippet_or_404(db, snippet_id, user.id)
    return templates.TemplateResponse(request, "snippets/form.html", {"user": user, "snippet": snippet})


@router.post("/{snippet_id}")
async def update_snippet(
    snippet_id: int, request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    snippet = _get_snippet_or_404(db, snippet_id, user.id)
    form = await request.form()
    snippet.title = (form.get("title") or "").strip()
    snippet.description = form.get("description") or ""
    snippet.tags = resolve_tags(db, form.get("tags") or "")
    _apply_files_from_form(db, snippet, form)
    db.commit()
    return RedirectResponse("/snippets", status_code=303)


@router.post("/{snippet_id}/files/{file_id}/content")
def update_snippet_file_content(
    snippet_id: int,
    file_id: int,
    content: str = Form(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    """Losse route om alleen de code van één bestand bij te werken -- gebruikt door de
    bijna-volledig-scherm snippet-viewer (app/static/js/snippets-list.js), zodat je code
    direct kunt aanpassen zonder naar het volledige bewerkformulier te hoeven (dat ook
    titel/tags/bestandenlijst beheert, wat hier niet nodig -- en dus ook niet per ongeluk
    aan te passen -- is)."""
    snippet = _get_snippet_or_404(db, snippet_id, user.id)
    file = next((f for f in snippet.files if f.id == file_id), None)
    if file is None:
        raise HTTPException(status_code=404, detail="Bestand niet gevonden")
    file.content = content
    db.commit()
    return {"ok": True}


@router.post("/{snippet_id}/delete")
def delete_snippet(snippet_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    snippet = _get_snippet_or_404(db, snippet_id, user.id)
    db.delete(snippet)
    db.commit()
    return RedirectResponse("/snippets", status_code=303)
