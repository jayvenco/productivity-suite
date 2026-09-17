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
- Kanban-bord met **swimlanes** (rijen); elke swimlane heeft haar **eigen kolommen**
  (start met Todo/In Progress/Done, per swimlane onafhankelijk uit te breiden) én een eigen,
  automatisch toegewezen **accentkleur** op haar kolommen (net als tags — direct herkenbaar
  welke kolom bij welke swimlane hoort), drag-and-drop tussen kolommen binnen een swimlane,
  kaarten los van taken
- Kanban-kaarten zijn **bewerkbaar** (titel, beschrijving, tags) en kunnen een **accentkleur**
  krijgen (kleurenpicker, zichtbaar als gekleurde rand links op de kaart)
- Checklists in kaartbeschrijvingen (`- [ ] item`) — aanklikbaar, direct persistent; een
  "+ Checklist-item"-knop voegt de syntax voor je toe
- Gedeeld tag-systeem (taken + kanban-kaarten): elke tag krijgt automatisch een eigen,
  stabiele kleur; filteren op tag, **sorteren** (deadline/titel/prioriteit/status) en
  **groeperen op tag** (dat is hier ook het "project"-alternatief — er is geen apart
  projectveld, tags dienen als project/categorie) op de takenlijst. Een taak met tags krijgt
  een lichte kleurtint op de rij, gebaseerd op de eerste tag
- Taken hebben een **prioriteitsvinkje** (★, sorteert bovenaan de takenlijst), een
  **snel-afvink-vinkje** (zet de taak direct op "done", of terug naar "todo") en een dunne
  **deadline-gradiëntbalk** onder de deadline-datum (halve breedte van die cel) die geleidelijk
  van antraciet naar donkeroranje kleurt naarmate de deadline nadert of al verstreken is
- Takenlijst-tabellen hebben **vaste kolombreedtes**, zodat ze uitlijnen ongeacht filter,
  sortering of groepering
- **Pomodoro-timer** als "Pomodoro"-menu-item in de sidebar i.p.v. een permanent zichtbaar
  blok: klik erop om een **zwevend, verplaatsbaar, semi-transparant paneel** rechtsonder in
  beeld te openen (instelbare werk-/pauze-duur, optioneel gekoppeld aan een taak, live
  aftellende ring-animatie, automatische overgang werk → pauze). Het paneel blijft op zijn
  plek zolang je door de app navigeert, en verschijnt automatisch weer als er al een sessie
  loopt; sluiten via het kruisje stopt de timer niet, verbergt 'm alleen. Geschiedenis
  zichtbaar op de taakpagina
- 4 thema's: Dracula, One Dark Pro, Nord, Light (wit met oranje accenten)
- **Notities**: lichte rich-text editor met knoppenbalk (vet, cursief, koppen, opsommingen,
  genummerde lijsten, links, code) — geen markdown-syntax typen nodig, wat je ziet is wat er
  opgeslagen wordt. Inhoud is HTML, server-side gesanitized (`bleach`) tegen XSS. Taggable met
  hetzelfde gedeelde tag-systeem (kleuren, filteren) als taken/kanban. De hele kaart in de
  lijstweergave is klikbaar om te bewerken, en een **selectievak per notitie** maakt
  bulk-acties mogelijk: meerdere notities in één keer verwijderen of er samen een tag aan
  toevoegen

Nog niet gebouwd: volledige kalenderweergave (maand/week), code snippets (link in de sidebar
toont "binnenkort"), CI/CD, backup/export-import, spraaknotities, LLM-koppeling.

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
3. Taak bewerken en status wijzigen naar "done". Op de takenlijst het snel-afvink-vinkje
   gebruiken → status wisselt direct tussen "todo" en "done", en de huidige
   sortering/groepering/filter blijft daarbij behouden (ook na filteren op status/tag).
4. Op een tag klikken in de takenlijst → filtert de lijst. Taken aanmaken met verschillende
   tags → controleer dat elke tag een eigen kleur heeft en dat de taakrij een lichte tint van
   die kleur krijgt. Sorteren op titel/prioriteit/status en groeperen op tag uitproberen, en
   controleren dat de kolommen precies uitlijnen tussen groepen/filters.
5. Naar Kanban gaan, een swimlane toevoegen (krijgt automatisch eigen Todo/In Progress/Done)
   en daar een eigen kolom aan toevoegen → controleer dat die kolom alleen in díe swimlane
   verschijnt. Een kaart aanmaken met een checklist (`- [ ] item`) → klik een checklist-item
   aan en herlaad de pagina om te controleren dat het aangevinkt blijft. Klik "Bewerken" op
   een kaart, geef 'm een titel/kleur/tags en controleer dat de gekleurde rand verschijnt en
   blijft na herladen.
6. Kaart verslepen naar een andere kolom/swimlane (drag-and-drop) → herlaad de pagina en
   controleer dat de cel-toewijzing bewaard is gebleven.
7. Klik op "Pomodoro" in de sidebar → het zwevende paneel opent rechtsonder. Sleep het paneel
   aan de titelbalk naar een andere plek. Start een timer (kies eventueel een taak) →
   controleer de leeglopende ring, de automatische overgang naar de pauze-fase, en dat
   navigeren naar een andere pagina het paneel op dezelfde plek en met de lopende timer laat
   staan. Sluit het paneel via het kruisje en open het opnieuw via het menu → de timer loopt
   gewoon door. Controleer op de taakpagina dat voltooide werk-sessies meetellen in de
   Pomodoro-historie.
8. Thema wisselen via de kleurenbolletjes in de sidebar (incl. het lichte thema) → voorkeur
   blijft na herladen/opnieuw inloggen behouden.
9. Naar Notities gaan, een notitie aanmaken: tekst selecteren en vet/cursief maken via de
   knoppenbalk, een kop toepassen, een lijst en een link toevoegen, plus tags → controleer dat
   de kaart in de lijstweergave de opmaak en gekleurde tags toont (elke tag een andere, bij
   aanmaak willekeurig gekozen kleur), en dat de kaart een lichte tint krijgt op basis van de
   eerste tag. Filteren op tag uitproberen. Klik ergens op een kaart (niet alleen de titel) →
   opent de bewerkpagina. Vink twee notities aan via het selectievakje → de bulk-balk
   verschijnt bovenaan; voeg een tag toe aan de selectie en controleer dat beide notities 'm
   krijgen zonder bestaande tags te verliezen, en test daarna bulk-verwijderen.
10. Uitloggen en controleren dat alle pagina's terug naar `/login` sturen.

## Architectuur

- **Backend**: FastAPI (async-vriendelijk, ingebouwde validatie/docs) + SQLAlchemy 2.0 ORM
  (zodat een latere Postgres-migratie mogelijk blijft zonder dat we er nu voor bouwen).
- **Frontend**: Server-rendered Jinja2 templates, progressive enhancement met vanilla JS
  (drag-and-drop) en Alpine/HTMX-ready (HTMX is al ingeladen voor latere fasen).
- **Auth**: Sessie-cookie met `itsdangerous`, wachtwoord-hashing via `passlib[bcrypt]`.
- **Kanban-kaarten** zijn losse entiteiten (geen 1-op-1 met Taken) — een kaart kan optioneel
  naar een taak verwijzen, maar dat is geen vereiste.
- **Swimlanes en kolommen**: `KanbanColumn` hangt aan een `KanbanSwimlane` (niet meer direct
  aan het bord), zodat elke swimlane haar eigen kolommenset heeft. Een nieuwe swimlane krijgt
  automatisch de standaardkolommen (Todo/In Progress/Done) mee als startpunt, daarna volledig
  onafhankelijk aan te passen.
- **Checklists** op kanban-kaarten zijn gewoon markdown (`- [ ] item`) in de bestaande
  beschrijving — geen apart datamodel; een klik op de checkbox schakelt de regel in de
  opgeslagen tekst om via een klein endpoint (`/kanban/cards/{id}/checklist-toggle`). Een
  "+ Checklist-item"-knop bij de beschrijving voegt de `- [ ] `-syntax voor je toe (je hoeft
   'm niet zelf te typen), en de herkenning is tolerant voor ontbrekende spaties
  (`-[ ]item` werkt ook).
- **Tag-kleuren zijn willekeurig**: elke nieuwe tag krijgt bij aanmaak een echt willekeurige
  `hsl(...)`-tint (`app/services/tags.py::generate_tag_color`), eenmalig bepaald en opgeslagen
  op de `Tag` zelf — dus stabiel voor die tag daarna, maar niet voorspelbaar uit de naam. Tags
  die vóór deze functie zijn aangemaakt (met de oude vaste grijstint) worden bij het opstarten
  eenmalig omgezet (`backfill_tag_colors`).
- **Swimlane-kleuren blijven wél naam-gebaseerd**: `app/services/colors.py::stable_hue()`
  levert een hash-gebaseerde kleurtint puur berekend uit de swimlane-naam (geen los kleurveld
  nodig) — bewust anders dan tags, want swimlane-namen zijn vaste categorieën (bv. "Werk"),
  waar je wilt dat dezelfde naam altijd dezelfde kleur teruggeeft (bv. na het per ongeluk
  verwijderen en opnieuw aanmaken van een swimlane).
- Rijtinten en kolomaccenten gebruiken telkens een transparante hsla-laag i.p.v. een vaste
  licht/donker kleur, zodat ze in elk thema goed leesbaar blijven.
- **Groeperen op tag**: een taak met meerdere tags verschijnt in elke bijbehorende groep
  (geen kunstmatige keuze voor "de hoofdtag"); taken zonder tag komen in een aparte
  "Zonder tag"-groep aan het eind.
- **Vaste kolombreedtes** (`.tasks-table { table-layout: fixed }` + `<colgroup>`): zonder dit
  berekent de browser de kolombreedtes per `<table>` op basis van alleen de inhoud van díe
  tabel, wat de kolommen liet verspringen tussen filters en tussen groepen (elke groep is een
  eigen `<table>`). Nu staat elke kolombreedte vast, ongeacht wat erin staat.
- **Snel-afvink-vinkje**: een losse `POST /tasks/{id}/toggle-done` die alleen de status
  wisselt tussen `todo` en `done` (i.p.v. het hele bewerk-formulier te doorlopen). De huidige
  sortering/groepering/filters worden als hidden fields meegestuurd zodat de redirect
  terugkomt op exact dezelfde weergave i.p.v. terug te vallen op de ongefilterde lijst
  (dezelfde aanpak is ook toegepast op de verwijder-knop).
- **Notities-editor**: een `contenteditable`-div met een knoppenbalk die
  `document.execCommand` gebruikt (vet, cursief, koppen, lijsten, links, inline code) —
  bewust geen externe editor-library, wat je ziet tijdens het typen is exact de opgeslagen
  HTML. Vóór het opslaan wordt de HTML server-side gesanitized (`app/services/richtext.py`,
  via `bleach`) tegen een vaste tag/attribuut-whitelist, want de inhoud wordt met `|safe`
  gerenderd en `contenteditable` kan in theorie geplakte HTML van buitenaf bevatten.
- **Notities-lijst — klikbare kaart + bulk-acties**: de hele kaart is klikbaar (via
  `app/static/js/notes-list.js`, dat klikken op checkbox/tags/links doorlaat maar de rest
  doorstuurt naar de bewerkpagina). Eén `<form>` omvat de hele grid plus de bulk-actiebalk;
  elke checkbox heet `note_ids` zodat de browser bij versturen automatisch alle aangevinkte
  id's meestuurt — geen JS nodig om een verborgen veld te synchroniseren. De twee
  submit-knoppen sturen naar een andere `formaction` (`/notes/bulk-delete` resp.
  `/notes/bulk-tag`) met dezelfde geselecteerde id's.
- **Pomodoro** bewaart alleen start-tijd + geplande duur per sessie; de countdown-ring wordt
  client-side berekend zodat een pagina-refresh niets verliest. Er is bewust geen pauzeknop
  (alleen start/stop) om de tijdsberekening simpel te houden.
- **Pomodoro-paneel als losse overlay**: `#pomodoro-float` staat buiten de `.layout`-div in
  `base.html` (fixed positioning t.o.v. het venster, niet t.o.v. de sidebar) en is standaard
  `hidden`. De "Pomodoro"-knop in de sidebar toggelt de zichtbaarheid; bij het laden van een
  pagina wordt het paneel automatisch getoond als er al een sessie loopt. Slepen gebeurt via
  `mousedown`/`mousemove`/`mouseup` op de titelbalk, geklemd binnen het viewport, met de
  positie bewaard in `localStorage` (per-browser gemak, geen server-state) zodat 'm na een
  refresh op dezelfde plek terugkomt.
- **Deadline-gradiëntbalk**: kleur wordt server-side berekend (`Task.urgency_color`) op basis
  van een venster van 14 dagen — antraciet (`rgb(63,63,70)`) ver van de deadline, lineair naar
  donkeroranje (`rgb(154,52,18)`) op de deadline zelf, en blijft donkeroranje bij een
  verstreken deadline (geen aparte roodstand).
- **Lichte, additive migraties** (`app/services/migrate.py`): nieuwe kolommen (zoals
  `priority`, `color` en `kanban_columns.swimlane_id`) worden bij het opstarten toegevoegd aan
  een bestaande SQLite-database als ze nog ontbreken. Bij de overstap naar per-swimlane
  kolommen worden bestaande kolommen automatisch aan de (eerste) swimlane van hun bord
  gekoppeld, zodat een update op een al draaiende installatie (bv. Unraid) geen data
  kwijtraakt. Geen Alembic voor deze schaal.
