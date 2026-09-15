# Productivity Suite

Persoonlijke, self-hosted productivity-app (Taken, Kanban, Notities, Kalender, Snippets, Pomodoro).
Single-container Docker-deployment met SQLite.

## Status: Fase 1 (MVP)

Gebouwd in deze fase:
- Docker-setup (Dockerfile + docker-compose.yml, SQLite-volume onder `./data`)
- SQLite-datamodel via SQLAlchemy (Users, Tasks, Tags, Kanban board/columns/swimlanes/cards)
- Sessie-based auth (single-user, seed-account bij eerste start)
- Taken: CRUD, deadline, status, tags, markdown-beschrijving
- Kanban-bord (kolommen Todo/In Progress/Done, drag-and-drop tussen kolommen, kaarten los van taken)
- Gedeeld tag-systeem (taken + kanban-kaarten), filteren op tag
- 3 thema's: Dracula, One Dark Pro, Nord — voorkeur opgeslagen per gebruiker

Nog niet gebouwd (latere fasen, zie build-prompt): Pomodoro-timer, kalenderweergave met
deadline-waarschuwing, swimlane-UI, notities-module, code snippets, resterende 7 thema's,
CI/CD, backup/export-import, spraaknotities, LLM-koppeling.

## Lokaal draaien

Met Docker (aanbevolen):

```bash
cp .env.example .env   # pas SECRET_KEY / DEFAULT_PASSWORD aan
docker compose up --build
```

App draait op http://localhost:8000. Standaard login: `admin` / wachtwoord uit `.env`
(`changeme` als je niets instelt — verander dit meteen na de eerste keer inloggen via
een toekomstige "wachtwoord wijzigen"-functie, die nog niet in Fase 1 zit).

Zonder Docker (lokale Python 3.12 venv):

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/uvicorn app.main:app --reload
```

## Tests

```bash
./.venv/bin/pytest
```

## Handmatig te testen (Fase 1)

1. Inloggen met het seed-account (`admin` / `changeme` of je eigen `.env`-waarden).
2. Nieuwe taak aanmaken met titel, beschrijving (markdown), deadline binnen 3 dagen en tags
   → controleer dat de "bijna deadline"-badge verschijnt op de takenlijst.
3. Taak bewerken en status wijzigen naar "done".
4. Op een tag klikken in de takenlijst → filtert de lijst.
5. Naar Kanban gaan, een kaart toevoegen aan een kolom met tags.
6. Kaart verslepen naar een andere kolom (drag-and-drop) → herlaad de pagina en controleer
   dat de kolom-toewijzing bewaard is gebleven.
7. Thema wisselen via de kleurenbolletjes in de sidebar → voorkeur blijft na herladen/opnieuw
   inloggen behouden.
8. Uitloggen en controleren dat alle pagina's terug naar `/login` sturen.

## Architectuur

- **Backend**: FastAPI (async-vriendelijk, ingebouwde validatie/docs) + SQLAlchemy 2.0 ORM
  (zodat een latere Postgres-migratie mogelijk blijft zonder dat we er nu voor bouwen).
- **Frontend**: Server-rendered Jinja2 templates, progressive enhancement met vanilla JS
  (drag-and-drop) en Alpine/HTMX-ready (HTMX is al ingeladen voor latere fasen).
- **Auth**: Sessie-cookie met `itsdangerous`, wachtwoord-hashing via `passlib[bcrypt]`.
- **Kanban-kaarten** zijn losse entiteiten (geen 1-op-1 met Taken) — een kaart kan optioneel
  naar een taak verwijzen, maar dat is geen vereiste.
- **Swimlanes** bestaan al in het datamodel (met een default "Algemeen"-lane per bord) zodat
  Fase 2 geen destructieve migratie nodig heeft; de UI toont ze pas vanaf Fase 2.
