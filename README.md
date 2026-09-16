# Productivity Suite

Persoonlijke, self-hosted productivity-app (Taken, Kanban, Notities, Kalender, Snippets, Pomodoro).
Single-container Docker-deployment met SQLite.

## Status: Fase 1 + delen van Fase 2

Gebouwd:
- Docker-setup (Dockerfile + docker-compose.yml, SQLite-volume onder `./data`)
- SQLite-datamodel via SQLAlchemy (Users, Tasks, Tags, Kanban board/columns/swimlanes/cards, Pomodoro-sessies)
- Sessie-based auth (single-user, seed-account, wachtwoord wijzigen via Account-pagina)
- Taken: CRUD, deadline, status, tags, markdown-beschrijving
- Sidebar-widget "Komende deadlines" (eerstvolgende 5 taken met deadline)
- Kanban-bord met **swimlanes** (rijen) × kolommen (Todo/In Progress/Done), drag-and-drop
  tussen elke cel, kaarten los van taken
- Kanban-kaarten zijn **bewerkbaar** (titel, beschrijving, tags) en kunnen een **accentkleur**
  krijgen (kleurenpicker, zichtbaar als gekleurde rand links op de kaart)
- Checklists in kaartbeschrijvingen (`- [ ] item`) — aanklikbaar, direct persistent
- Gedeeld tag-systeem (taken + kanban-kaarten), filteren op tag
- Taken hebben een **prioriteitsvinkje** (★, sorteert bovenaan de takenlijst) en een dunne
  **deadline-gradiëntbalk** die geleidelijk van groen naar oranje/rood kleurt naarmate de
  deadline nadert (of verstreken is)
- **Pomodoro-timer** in de sidebar: instelbare werk-/pauze-duur, optioneel gekoppeld aan
  een taak, live aftellende ring-animatie, automatische overgang werk → pauze, geschiedenis
  zichtbaar op de taakpagina
- 4 thema's: Dracula, One Dark Pro, Nord, Light (wit met oranje accenten)

Nog niet gebouwd: volledige kalenderweergave (maand/week), notities-module, code snippets
(links in de sidebar tonen "binnenkort"), CI/CD, backup/export-import, spraaknotities,
LLM-koppeling.

## Configuratie

Geen `.env`-bestand of omgevingsvariabelen nodig. Bij de eerste start:
- wordt een sessie-secret-key automatisch gegenereerd en opgeslagen in `data/.secret_key`
  (blijft geldig na herstarts/updates, zolang het data-volume bewaard blijft);
- wordt een seed-account aangemaakt: gebruikersnaam `admin`, wachtwoord `admin`.

Na de eerste login toont de app een waarschuwing zolang je het standaardwachtwoord
gebruikt. Wijzig gebruikersnaam/wachtwoord via de **Account**-pagina in de sidebar.

## Lokaal draaien

Met Docker (aanbevolen):

```bash
docker compose up --build
```

App draait op http://localhost:8000. Standaard login: `admin` / `admin`.

Zonder Docker (lokale Python 3.12 venv):

```bash
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/uvicorn app.main:app --reload
```

## Installeren op Unraid

```bash
bash scripts/install-unraid.sh
```

Draai dit via SSH op de Unraid-server (of als "User Script"). Het script:
1. clonet/update de code naar `/mnt/user/appdata/productivity-suite/src`;
2. bouwt de Docker image lokaal (`docker build`);
3. start/herstart de container `productivity-suite` op poort **8887** (standaard, want
   8000 is op Unraid vaak al bezet), met de data persistent in
   `/mnt/user/appdata/productivity-suite/data`.

Opnieuw draaien = updaten naar de laatste commit op `main` zonder dataverlies.
Instelbaar via omgevingsvariabelen bij het aanroepen, bv. een andere poort:

```bash
HOST_PORT=9000 bash scripts/install-unraid.sh
```

## Tests

```bash
./.venv/bin/pytest
```

## Handmatig te testen

1. Inloggen met het seed-account (`admin` / `admin`) → controleer dat de
   standaardwachtwoord-waarschuwing verschijnt, wijzig het wachtwoord via Account en
   controleer dat de waarschuwing verdwijnt.
2. Nieuwe taak aanmaken met titel, beschrijving (markdown), deadline binnen 3 dagen en tags
   → controleer dat de "bijna deadline"-badge verschijnt op de takenlijst én in het
   "Komende deadlines"-widgetje in de sidebar.
3. Taak bewerken en status wijzigen naar "done".
4. Op een tag klikken in de takenlijst → filtert de lijst.
5. Naar Kanban gaan, een swimlane toevoegen en een kaart aanmaken met een checklist
   (`- [ ] item`) → klik een checklist-item aan en herlaad de pagina om te controleren dat
   het aangevinkt blijft. Klik "Bewerken" op een kaart, geef 'm een titel/kleur/tags en
   controleer dat de gekleurde rand verschijnt en blijft na herladen.
6. Kaart verslepen naar een andere kolom/swimlane (drag-and-drop) → herlaad de pagina en
   controleer dat de cel-toewijzing bewaard is gebleven.
7. Pomodoro-timer starten (kies eventueel een taak) → controleer de leeglopende ring, de
   automatische overgang naar de pauze-fase, en dat een refresh de lopende timer niet reset.
   Controleer op de taakpagina dat voltooide werk-sessies meetellen in de Pomodoro-historie.
8. Thema wisselen via de kleurenbolletjes in de sidebar (incl. het lichte thema) → voorkeur
   blijft na herladen/opnieuw inloggen behouden.
9. Uitloggen en controleren dat alle pagina's terug naar `/login` sturen.

## Architectuur

- **Backend**: FastAPI (async-vriendelijk, ingebouwde validatie/docs) + SQLAlchemy 2.0 ORM
  (zodat een latere Postgres-migratie mogelijk blijft zonder dat we er nu voor bouwen).
- **Frontend**: Server-rendered Jinja2 templates, progressive enhancement met vanilla JS
  (drag-and-drop) en Alpine/HTMX-ready (HTMX is al ingeladen voor latere fasen).
- **Auth**: Sessie-cookie met `itsdangerous`, wachtwoord-hashing via `passlib[bcrypt]`.
- **Kanban-kaarten** zijn losse entiteiten (geen 1-op-1 met Taken) — een kaart kan optioneel
  naar een taak verwijzen, maar dat is geen vereiste.
- **Swimlanes** zijn volledig verwerkt in de UI: het bord toont een grid van swimlane-rijen ×
  kolommen, drag-and-drop werkt tussen elke cel.
- **Checklists** op kanban-kaarten zijn gewoon markdown (`- [ ] item`) in de bestaande
  beschrijving — geen apart datamodel; een klik op de checkbox schakelt de regel in de
  opgeslagen tekst om via een klein endpoint (`/kanban/cards/{id}/checklist-toggle`).
- **Pomodoro** bewaart alleen start-tijd + geplande duur per sessie; de countdown-ring wordt
  client-side berekend zodat een pagina-refresh niets verliest. Er is bewust geen pauzeknop
  (alleen start/stop) om de tijdsberekening simpel te houden.
- **Deadline-gradiëntbalk**: kleur wordt server-side berekend (`Task.urgency_color`) op basis
  van een venster van 14 dagen — groen ver van de deadline, oranje dichtbij, rood bij een
  verstreken deadline.
- **Lichte, additive migraties** (`app/services/migrate.py`): nieuwe kolommen (zoals
  `priority` en `color`) worden bij het opstarten toegevoegd aan een bestaande SQLite-database
  als ze nog ontbreken, zodat een update op een al draaiende installatie (bv. Unraid) geen
  data kwijtraakt. Geen Alembic voor deze schaal.
