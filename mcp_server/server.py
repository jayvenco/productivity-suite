"""MCP-server (stdio) voor Productivity Suite.

Een dunne laag bovenop de JSON-API (/api/v1, zie AGENT_API.md): elke tool roept één
API-route aan. Draait los van de app, met een eigen venv (de `mcp`-library trekt een nieuwere
Starlette binnen dan de app zelf pint).

Configuratie via omgevingsvariabelen:
  PRODUCTIVITY_URL    basis-URL van de app, bv. http://192.168.2.200:8887
  PRODUCTIVITY_TOKEN  API-token (Account -> API-token)
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("productivity-suite")

_client: httpx.Client | None = None


def _http() -> httpx.Client:
    global _client
    if _client is None:
        base = os.environ.get("PRODUCTIVITY_URL", "http://localhost:8887").rstrip("/")
        token = os.environ.get("PRODUCTIVITY_TOKEN", "")
        _client = httpx.Client(
            base_url=f"{base}/api/v1", headers={"Authorization": f"Bearer {token}"}, timeout=30
        )
    return _client


def _call(method: str, path: str, *, params: dict | None = None, json: Any = None) -> Any:
    """Roept de API aan en geeft de JSON terug; bij een fout een duidelijke melding met de
    `detail` van de server zodat de agent weet wat er mis was."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    response = _http().request(method, path, params=params, json=json)
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"API-fout {response.status_code} bij {method} {path}: {detail}")
    return response.json()


def _drop_unset(**fields: Any) -> dict:
    return {k: v for k, v in fields.items() if v is not None}


# ---- Algemeen ----


@mcp.tool()
def health() -> dict:
    """Controleert verbinding en token."""
    return _call("GET", "/health")


# ---- Taken ----


@mcp.tool()
def list_tasks(
    status: str | None = None,
    tag: str | None = None,
    priority: bool | None = None,
    due_before: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Lijst taken, nieuwste eerst. status: 'open', 'done' of 'archived' (leeg = alles behalve
    gearchiveerd). due_before: datum YYYY-MM-DD. Geeft {items, total, limit, offset}."""
    return _call(
        "GET",
        "/tasks",
        params={"status": status, "tag": tag, "priority": priority, "due_before": due_before,
                "limit": limit, "offset": offset},
    )


@mcp.tool()
def get_task(task_id: int) -> dict:
    """Haalt één taak op."""
    return _call("GET", f"/tasks/{task_id}")


@mcp.tool()
def create_task(
    title: str,
    description: str = "",
    deadline: str | None = None,
    tags: str = "",
    priority: bool = False,
) -> dict:
    """Maakt een taak. deadline: YYYY-MM-DD. tags: komma-gescheiden ('werk, urgent')."""
    return _call("POST", "/tasks", json=_drop_unset(
        title=title, description=description, deadline=deadline, tags=tags, priority=priority))


@mcp.tool()
def update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    deadline: str | None = None,
    tags: str | None = None,
    priority: bool | None = None,
    daily_task: bool | None = None,
    done: bool | None = None,
) -> dict:
    """Wijzigt alleen de meegegeven velden. done=true vinkt af, done=false zet terug naar open.
    tags vervangt alle bestaande tags. (Een deadline wissen kan niet via deze tool.)"""
    return _call("PATCH", f"/tasks/{task_id}", json=_drop_unset(
        title=title, description=description, deadline=deadline, tags=tags,
        priority=priority, daily_task=daily_task, done=done))


@mcp.tool()
def delete_task(task_id: int) -> dict:
    """Verwijdert een taak definitief."""
    return _call("DELETE", f"/tasks/{task_id}")


@mcp.tool()
def restore_task(task_id: int) -> dict:
    """Haalt een (gearchiveerde) taak terug naar de open takenlijst."""
    return _call("POST", f"/tasks/{task_id}/restore")


# ---- Notities ----


@mcp.tool()
def list_notes(tag: str | None = None, is_temp: bool | None = None, limit: int = 100, offset: int = 0) -> dict:
    """Lijst notities, nieuwste eerst. is_temp=true toont alleen tijdelijke notities."""
    return _call("GET", "/notes", params={"tag": tag, "is_temp": is_temp, "limit": limit, "offset": offset})


@mcp.tool()
def get_note(note_id: int) -> dict:
    """Haalt één notitie op (content is HTML)."""
    return _call("GET", f"/notes/{note_id}")


@mcp.tool()
def create_note(title: str, content: str = "", tags: str = "") -> dict:
    """Maakt een notitie. content is HTML (bv. '<p>tekst</p>'); onveilige HTML wordt verwijderd."""
    return _call("POST", "/notes", json={"title": title, "content": content, "tags": tags})


@mcp.tool()
def update_note(
    note_id: int,
    title: str | None = None,
    content: str | None = None,
    tags: str | None = None,
    is_temp: bool | None = None,
) -> dict:
    """Wijzigt alleen de meegegeven velden. is_temp=true: wordt na een week automatisch verwijderd."""
    return _call("PATCH", f"/notes/{note_id}", json=_drop_unset(
        title=title, content=content, tags=tags, is_temp=is_temp))


@mcp.tool()
def delete_note(note_id: int) -> dict:
    """Verwijdert een notitie definitief."""
    return _call("DELETE", f"/notes/{note_id}")


# ---- Snippets ----


@mcp.tool()
def list_snippets(tag: str | None = None, limit: int = 100, offset: int = 0) -> dict:
    """Lijst code-snippets inclusief bestanden en inhoud."""
    return _call("GET", "/snippets", params={"tag": tag, "limit": limit, "offset": offset})


@mcp.tool()
def get_snippet(snippet_id: int) -> dict:
    """Haalt één snippet op, inclusief alle bestanden en code."""
    return _call("GET", f"/snippets/{snippet_id}")


@mcp.tool()
def create_snippet(title: str, files: list[dict], tags: str = "") -> dict:
    """Maakt een snippet. files: lijst van {"filename": "a.py", "language": "python",
    "content": "..."}; minstens één bestand."""
    return _call("POST", "/snippets", json={"title": title, "tags": tags, "files": files})


@mcp.tool()
def update_snippet(
    snippet_id: int,
    title: str | None = None,
    description: str | None = None,
    tags: str | None = None,
    files: list[dict] | None = None,
) -> dict:
    """Wijzigt alleen de meegegeven velden. Geef je files mee, dan vervangt dat ALLE bestanden."""
    return _call("PATCH", f"/snippets/{snippet_id}", json=_drop_unset(
        title=title, description=description, tags=tags, files=files))


@mcp.tool()
def delete_snippet(snippet_id: int) -> dict:
    """Verwijdert een snippet definitief."""
    return _call("DELETE", f"/snippets/{snippet_id}")


# ---- Kanban ----


@mcp.tool()
def get_kanban_board() -> dict:
    """Haalt het hele kanbanbord op: swimlanes -> kolommen -> kaarten. Gebruik dit om de
    swimlane_id/column_id's te vinden voor create_kanban_card en move_kanban_card."""
    return _call("GET", "/kanban")


@mcp.tool()
def list_kanban_cards(
    swimlane_id: int | None = None, column_id: int | None = None, tag: str | None = None,
    limit: int = 100, offset: int = 0,
) -> dict:
    """Lijst kanban-kaarten, optioneel gefilterd op swimlane, kolom of tag."""
    return _call("GET", "/kanban/cards", params={
        "swimlane_id": swimlane_id, "column_id": column_id, "tag": tag, "limit": limit, "offset": offset})


@mcp.tool()
def create_kanban_card(
    title: str,
    description: str = "",
    tags: str = "",
    color: str | None = None,
    swimlane_id: int | None = None,
    column_id: int | None = None,
) -> dict:
    """Maakt een kaart. Zonder swimlane_id én column_id komt hij in de eerste cel van het bord.
    Checklist-items: zet '- [ ] stap' op aparte regels in description."""
    return _call("POST", "/kanban/cards", json=_drop_unset(
        title=title, description=description, tags=tags, color=color,
        swimlane_id=swimlane_id, column_id=column_id))


@mcp.tool()
def update_kanban_card(
    card_id: int,
    title: str | None = None,
    description: str | None = None,
    tags: str | None = None,
    color: str | None = None,
) -> dict:
    """Wijzigt alleen de meegegeven velden (color als '#rrggbb'; lege tekst '' wist de kleur)."""
    return _call("PATCH", f"/kanban/cards/{card_id}", json=_drop_unset(
        title=title, description=description, tags=tags, color=color))


@mcp.tool()
def move_kanban_card(card_id: int, swimlane_id: int, column_id: int, position: int = 0) -> dict:
    """Verplaatst een kaart naar een kolom (die moet bij de opgegeven swimlane horen)."""
    return _call("POST", f"/kanban/cards/{card_id}/move", json={
        "swimlane_id": swimlane_id, "column_id": column_id, "position": position})


@mcp.tool()
def toggle_kanban_checklist_item(card_id: int, line_index: int) -> dict:
    """Vinkt een checklist-regel in de kaartbeschrijving aan/uit. line_index: regelnummer in de
    beschrijving, beginnend bij 0."""
    return _call("POST", f"/kanban/cards/{card_id}/checklist-toggle", json={"line_index": line_index})


@mcp.tool()
def delete_kanban_card(card_id: int) -> dict:
    """Verwijdert een kaart definitief."""
    return _call("DELETE", f"/kanban/cards/{card_id}")


@mcp.tool()
def list_kanban_swimlanes() -> dict:
    """Lijst swimlanes met hun kolommen."""
    return _call("GET", "/kanban/swimlanes")


@mcp.tool()
def create_kanban_swimlane(name: str) -> dict:
    """Maakt een swimlane met de 5 standaardkolommen (Backlog/To Do/In Progress/Review/Done)."""
    return _call("POST", "/kanban/swimlanes", json={"name": name})


@mcp.tool()
def rename_kanban_swimlane(swimlane_id: int, name: str) -> dict:
    """Hernoemt een swimlane."""
    return _call("PATCH", f"/kanban/swimlanes/{swimlane_id}", json={"name": name})


@mcp.tool()
def delete_kanban_swimlane(swimlane_id: int) -> dict:
    """Verwijdert een swimlane inclusief al zijn kolommen en kaarten. De laatste swimlane van het
    bord kan niet verwijderd worden."""
    return _call("DELETE", f"/kanban/swimlanes/{swimlane_id}")


if __name__ == "__main__":
    mcp.run()
