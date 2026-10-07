# Productivity Suite — API-handleiding voor agents

Basis-URL: `http://192.168.2.200:8887/api/v1`
Alle verzoeken en antwoorden zijn JSON. Volledige routelijst met velden: `GET /openapi.json`.

## Authenticatie
Elk verzoek heeft deze header nodig (token aan te maken onder Account → API-token):

```
Authorization: Bearer <token>
Content-Type: application/json
```

Ontbrekende/ongeldige token → `401` met `{"detail": "..."}`. Verbinding testen: `GET /health` → `{"status":"ok","auth":"ok"}`.

## Conventies
- **Lijsten**: `GET /tasks` geeft `{"items": [...], "total": N, "limit": 100, "offset": 0}`. Pagineer met `?limit=` (max 500) en `?offset=`. Nieuwste eerst.
- **Aanmaken**: `POST` → `200` met het object (incl. `id`). **Bijwerken**: `PATCH` → `200` met het object; stuur alleen de velden die veranderen (`null` wist deadline/kleur). **Verwijderen**: `DELETE` → `{"deleted": true, "id": N}`.
- **Tags**: erin als komma-gescheiden string (`"werk, urgent"`, een lijst mag ook), eruit als lijst. Een PATCH met `tags` vervangt alle tags.
- Fouten: onbekend id `404`, ongeldige invoer `422`, lege titel `400`.

## Taken (`/tasks`)
| Actie | Verzoek |
|---|---|
| Aanmaken | `POST /tasks` `{"title": "...", "description": "", "deadline": "2026-12-31", "tags": "werk", "priority": false}` |
| Lijst | `GET /tasks?status=open\|done\|archived&tag=werk&priority=true&due_before=2026-12-31` |
| Ophalen | `GET /tasks/{id}` |
| Bijwerken | `PATCH /tasks/{id}` — velden: `title`, `description`, `deadline`, `tags`, `priority`, `daily_task`, `done` |
| Afvinken / terugzetten | `PATCH {"done": true}` of `POST /tasks/{id}/toggle-done` |
| Uit archief halen | `POST /tasks/{id}/restore` |
| Verwijderen | `DELETE /tasks/{id}` |

Afgeronde taken verdwijnen 8 uur na afronden naar het archief (`status=archived`), en worden daar na 30 dagen definitief verwijderd. Zonder `status` zie je alles behalve gearchiveerde taken.

## Notities (`/notes`)
`POST /notes` `{"title", "content" (HTML), "tags"}` · `GET /notes?tag=&is_temp=` · `GET|PATCH|DELETE /notes/{id}` (PATCH: `title`, `content`, `tags`, `is_temp`).
`is_temp: true` = wordt na een week automatisch verwijderd. HTML in `content` wordt opgeschoond (scripts e.d. verdwijnen).

## Snippets (`/snippets`)
`POST /snippets` `{"title", "tags", "files": [{"filename": "a.py", "language": "python", "content": "..."}]}` (minstens 1 bestand) · `GET /snippets?tag=` · `GET|PATCH|DELETE /snippets/{id}`.
`GET` geeft altijd de bestanden mét inhoud. PATCH: `title`, `description`, `tags`, en optioneel `files` (vervangt alle bestanden).

## Kanban (`/kanban`)
- `GET /kanban` — heel bord: swimlanes → kolommen → kaarten. Haal hier de `swimlane_id`/`column_id`'s vandaan.
- Kaart aanmaken: `POST /kanban/cards` `{"title", "description", "tags", "color", "swimlane_id", "column_id"}` (zonder swimlane/kolom komt hij in de eerste cel).
- `GET /kanban/cards?swimlane_id=&column_id=&tag=` · `GET|PATCH|DELETE /kanban/cards/{id}` (PATCH: `title`, `description`, `tags`, `color`).
- Verplaatsen: `POST /kanban/cards/{id}/move` `{"swimlane_id": 1, "column_id": 3, "position": 0}` (de kolom moet bij die swimlane horen).
- Checklist: items staan in `description` als `- [ ] stap` / `- [x] stap`; voortgang in `checklist: {done, total}`. Afvinken: `POST /kanban/cards/{id}/checklist-toggle` `{"line_index": 0}` (regelnummer in de beschrijving, vanaf 0).
- Swimlanes: `GET|POST /kanban/swimlanes` (`{"name"}`; een nieuwe krijgt 5 standaardkolommen) · `PATCH|DELETE /kanban/swimlanes/{id}` (de laatste swimlane kan niet verwijderd worden).

## Voorbeeld
```bash
BASE=http://192.168.2.200:8887/api/v1
H=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

curl -s -X POST "${H[@]}" $BASE/tasks -d '{"title":"Offerte sturen","tags":"werk"}'
curl -s "${H[@]}" "$BASE/tasks?status=open&tag=werk"
curl -s -X PATCH "${H[@]}" $BASE/tasks/12 -d '{"done": true}'
curl -s -X DELETE "${H[@]}" $BASE/tasks/12
```
