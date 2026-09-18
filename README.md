# Productivity Suite

Persoonlijke, self-hosted productivity-app (Taken, Kanban, Notities, Kalender, Snippets, Pomodoro).
Single-container Docker-deployment met SQLite.

## Status: Fase 1 + Fase 2 (kalender toegevoegd)

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
  krijgen (kleurenpicker, zichtbaar als gekleurde rand links op de kaart). Bewerken opent een
  **grotere, gecentreerde modal** (i.p.v. inline in de smalle kolom) met een **opmaak-werkbalk**
  (vet, cursief, kop, opsomming, code, en een link-knop die een URL + linktekst vraagt en er
  een klikbare markdown-link van maakt)
- Checklists in kaartbeschrijvingen (`- [ ] item`) — aanklikbaar, direct persistent; een
  "☑ Item"-knop op de werkbalk voegt de syntax voor je toe
- Gedeeld tag-systeem (taken + kanban-kaarten): elke tag krijgt automatisch een eigen,
  stabiele kleur; **sorteren** (deadline/titel/prioriteit/status) en **groeperen op tag**
  (dat is hier ook het "project"-alternatief — er is geen apart projectveld, tags dienen als
  project/categorie) op de takenlijst, met tag-groepen die je individueel kunt **in-/uitklappen**
  (status per groep onthouden in `localStorage`). **Filteren op tags** gaat via aanklikbare
  tag-checkboxes boven de lijst (meerdere tegelijk aan te vinken, OR-logica: een taak met
  minstens één van de aangevinkte tags blijft zichtbaar) — de taakrij zelf krijgt geen
  kleurtint meer op basis van de tag, alleen de tag-badge zelf is gekleurd
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
- 5 thema's: Dracula, One Dark Pro, Nord, Light (wit met oranje accenten), nexmail (graphite
  achtergrond met signaalgroen accent en het lettertype van nexmail — Space Grotesk voor
  koppen, IBM Plex Sans voor lopende tekst)
- **Weergave-instellingen** (Account → Weergave): los van het thema kiesbaar **lettertype**
  (14 opties — systeemstandaard, de leesletters Inter/Roboto/Open Sans/Lato/Poppins/Nunito/
  Source Sans 3/Merriweather/Fira Sans, en de monospace/code-letters Hack/JetBrains Mono/
  Fira Code/Consolas), **lettergrootte** (13–18px) en **compactheid** (comfortabel/compact,
  verkleint de ruimte tussen tekst en elementen door de sidebar, tabellen, kaarten en formulieren)
- Kanban-**swimlanes zijn in-/uitklapbaar**: klik op de swimlane-titel om de rij te verbergen.
  Status wordt per bord onthouden in `localStorage` (client-side, geen serverstate nodig voor
  een enkele gebruiker)
- **Notities**: lichte rich-text editor met knoppenbalk (vet, cursief, koppen, opsommingen,
  genummerde lijsten, links, code) — geen markdown-syntax typen nodig, wat je ziet is wat er
  opgeslagen wordt. Inhoud is HTML, server-side gesanitized (`bleach`) tegen XSS. Taggable met
  hetzelfde gedeelde tag-systeem (kleuren, filteren) als taken/kanban. De hele kaart in de
  lijstweergave is klikbaar om te bewerken, en een **selectievak per notitie** maakt
  bulk-acties mogelijk: meerdere notities in één keer verwijderen of er samen een tag aan
  toevoegen
- **Code snippets** (ByteStash-stijl): een snippet kan **meerdere bestanden** bevatten (bv.
  `main.py` + `requirements.txt` bij elkaar), elk met een eigen taal voor **syntax
  highlighting** (highlight.js) — de taal wordt **automatisch afgeleid uit de
  bestandsextensie** zodra je een bestandsnaam typt (bv. `config.json` → json,
  `app.py` → python), en blijft daarna gewoon handmatig aan te passen via de select. Kaarten
  staan **in een raster** (net als notities) en **standaard ingeklapt** (alleen titel, tags en
  bestandsnamen) — klik erop om de code compact binnen die kaart te tonen, i.p.v. een regel
  die over het hele werkscherm uitrekt. Eén zoekveld doorzoekt titel, tag én code-inhoud
  tegelijk, taggable met hetzelfde gedeelde tag-systeem
- **Kalender** met een **maand-** en **weekweergave** (te wisselen via de knoppen boven het
  rooster), navigatie met vorige/volgende en een "Vandaag"-knop, simpel/strak vormgegeven:
  één doorlopend raster met dunne lijnen tussen de dagen (geen losse "kaartjes" per dag),
  vandaag als een gekleurd rond bolletje om het dagnummer, en items als een klein gekleurd
  stipje + titel i.p.v. een gevulde badge. Toont twee soorten items door elkaar: **eigen
  afspraken** (titel, datum, beschrijving, tags — CRUD via `/calendar/events`, stipkleur volgt
  de eerste tag) en, puur ter info, **taken met een deadline** (klikbaar naar de taak,
  doorgestreept als de taak al "done" is, altijd een geel stipje). Elke dag heeft een
  "+"-knop (verschijnt bij hover) die direct een nieuwe afspraak opent met die datum
  vooringevuld
- **Mini-kalender in de sidebar**: een compact maandoverzicht op elke pagina, met een **rood
  stipje** op elke dag die een taak-deadline of afspraak heeft. Klik op een dag om direct
  (zonder de pagina te verlaten) een **taak aan te maken met die dag als deadline** — verschijnt
  meteen in de takenlijst en het "Komende deadlines"-widgetje. De maandnaam bovenin is ook een
  link naar de volledige kalenderpagina (maand-/weekweergave)

Nog niet gebouwd: CI/CD, backup/export-import, spraaknotities, LLM-koppeling.

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
4. Taken aanmaken met verschillende tags → controleer dat elke tag een eigen kleur heeft en
   dat de taakrij zelf geen kleurtint krijgt (alleen de tag-badge is gekleurd). Meerdere
   tag-checkboxes boven de lijst aanvinken → filtert op taken met minstens één van die tags.
   Sorteren op titel/prioriteit/status en groeperen op tag uitproberen, een tag-groep
   in-/uitklappen (herlaad de pagina en controleer dat de klap-status bewaard is gebleven), en
   controleren dat de kolommen precies uitlijnen tussen groepen/filters.
5. Naar Kanban gaan, een swimlane toevoegen (krijgt automatisch eigen Todo/In Progress/Done)
   en daar een eigen kolom aan toevoegen → controleer dat die kolom alleen in díe swimlane
   verschijnt. Een kaart aanmaken met een checklist (`- [ ] item`) → klik een checklist-item
   aan en herlaad de pagina om te controleren dat het aangevinkt blijft. Klik "Bewerken" op
   een kaart → een grotere, gecentreerde modal opent met een opmaak-werkbalk. Selecteer tekst
   en klik Vet/Cursief, en probeer de Link-knop (vraagt om een URL) → controleer na opslaan
   dat de kaart een klikbare link toont. Geef de kaart ook een titel/kleur/tags en controleer
   dat de gekleurde rand verschijnt en blijft na herladen. Klik op de achtergrond (backdrop)
   of "Annuleren" om de modal te sluiten zonder op te slaan.
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
10. Naar Snippets gaan, een snippet aanmaken met titel + tags, en via "+ Bestand toevoegen"
    een tweede bestand met een andere taal toevoegen (bv. `main.py` als python en
    `requirements.txt` als plaintext) → controleer dat de kaart in de lijst standaard
    ingeklapt staat (alleen titel/tags/bestandsnamen); klik erop om de code met syntax
    highlighting te tonen, en nogmaals om weer in te klappen. Zoek op een woord dat alleen in
    de tag van één snippet voorkomt en daarna op een woord dat alleen in de titel voorkomt →
    beide vinden de juiste snippet. Filteren op tag uitproberen.
11. Naar Kalender gaan (maandweergave staat standaard open) → controleer dat vandaag
    gemarkeerd is. Klik de "+" op een dag om een afspraak toe te voegen (datum staat al
    vooringevuld) met een titel en tag → verschijnt terug op die dag, gekleurd naar de tag.
    Maak een taak met een deadline in dezelfde maand → verschijnt ook in de kalender, met een
    andere randkleur dan afspraken, en doorgestreept zodra je 'm op "done" zet. Wissel naar de
    weekweergave en test Vorige/Volgende/Vandaag in beide weergaves.
12. In de sidebar op een lege dag in de mini-kalender klikken (bv. op de Notities-pagina, niet
    op Taken) → een klein formulier verschijnt met die datum, geen paginawissel. Typ een titel
    en klik "+ Taak" → een rood stipje verschijnt direct op die dag, en de taak staat na een
    bezoek aan de takenlijst met de juiste deadline. Blader met de pijltjes naar een andere
    maand en terug, en klik op de maandnaam bovenin → opent de volledige kalenderpagina op die
    maand.
13. Uitloggen en controleren dat alle pagina's terug naar `/login` sturen.

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
- **Snippets — meerdere bestanden per snippet**: `Snippet` en `SnippetFile` zijn losse
  modellen (1-op-N), zodat één snippet bv. `main.py` + `requirements.txt` samen kan bevatten
  zoals bij ByteStash. Het formulier gebruikt geen indexed field-namen; alle
  `filename`/`language`/`content`-velden delen dezelfde naam en worden server-side via
  `request.form().getlist(...)` op volgorde bij elkaar gezet (`_apply_files_from_form`). Bij
  bewerken worden bestaande bestanden simpelweg vervangen (`snippet.files.clear()` + opnieuw
  aanmaken) i.p.v. een diff bij te houden — voor deze schaal eenvoudiger en robuuster dan
  bestanden individueel bijwerken.
- **Snippets — bestand toevoegen/verwijderen in de browser**: `app/static/js/snippets.js`
  kloont het laatste bestand-blok i.p.v. de talenlijst te dupliceren in JS, en maakt de kloon
  leeg. Minstens één bestand blijft altijd staan.
- **Snippets — taal uit extensie**: een `EXTENSION_TO_LANGUAGE`-mapping in hetzelfde bestand
  luistert naar `input`-events op het bestandsnaam-veld en zet de taal-select automatisch op
  basis van de extensie (`.py` → python, `.json` → json, ...). Puur een gemaksfunctie op het
  moment van typen — er wordt niets herberekend of afgedwongen na het opslaan, dus een
  handmatige aanpassing van de select blijft altijd mogelijk en behouden.
- **Snippets — syntax highlighting**: highlight.js via CDN, alleen geladen op de lijstpagina.
  Zoeken (`?q=`) filtert op titel, tag-naam ÓF code-inhoud in één keer
  (`Snippet.tags.any(Tag.name.ilike(...))` / `Snippet.files.any(SnippetFile.content.ilike(...))`).
- **Snippets — standaard ingeklapt**: de code (`.snippet-files`) staat standaard `hidden`; een
  klik op de titel (`app/static/js/snippets-list.js`) toont/verbergt 'm. `hljs.highlightAll()`
  verwerkt de code-blokken sowieso bij het laden, ook terwijl ze verborgen zijn — highlight.js
  werkt op de DOM, niet op wat er zichtbaar is.
- **Snippets — raster i.p.v. volle-breedte rij**: `.snippets-list` gebruikt dezelfde
  `grid-template-columns: repeat(auto-fill, minmax(...px, 1fr))`-aanpak als `.notes-grid`,
  met `align-items: start` zodat een opengeklapte kaart de rijhoogte van de hele grid-rij niet
  optrekt voor zijn buren, en `min-width: 0` op de kaart zodat de `<pre>`-code binnen zijn
  eigen kolom horizontaal scrollt i.p.v. de kolombreedte op te rekken.
- **Kanban-kaart bewerken als modal**: `.card-edit-form.kanban-modal` gebruikt
  `position: fixed` + een losse backdrop-div, dus geen JS-herstructurering nodig — alleen CSS
  om de bestaande, per-kaart formulieren gecentreerd en groter te tonen i.p.v. inline in de
  smalle kolom.
- **Kanban-kaart — markdown-werkbalk i.p.v. rich text**: bewust een aparte aanpak dan de
  notitie-editor (die is `contenteditable` + HTML). Kanban-kaarten gebruiken nog steeds platte,
  regel-gebaseerde markdown omdat de checklist-functie (`- [ ] item`) daarop leunt; een
  contenteditable-editor zou die regel-gebaseerde herkenning breken. De werkbalk
  (`app/static/js/markdown-toolbar.js`) manipuleert daarom de tekst in een gewone `<textarea>`
  (selectie omwikkelen, regels prefixen, markdown-links invoegen) i.p.v. `execCommand`.
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
- **Lettertype/lettergrootte/compactheid**: opgeslagen op `User` (`font_family`, `font_size`,
  `density`), gezet via `POST /settings/appearance` vanaf de "Weergave"-sectie op de
  Account-pagina. `base.html` zet ze als `data-font`/`data-density`-attributen en een
  `--font-size-base`-CSS-variabele op `<html>`; `app.css` bevat per lettertype een
  `[data-font="..."]`-regel die `--font-sans`/`--font-heading` overschrijft (los van het
  actieve thema, dus een gekozen lettertype wint altijd van het thema-lettertype), en een
  `[data-density="compact"]`-blok met gerichte, kleinere padding/margin/gap-waarden voor de
  belangrijkste plekken (sidebar, tabellen, kaarten, formulieren) — geen volledige
  spacing-schaal, want dat had elke losse padding/margin in het bestand moeten aanraken.
- **Monospace-lettertypes (Hack/JetBrains Mono/Fira Code/Consolas)**: Hack staat niet in de
  Google Fonts-catalogus en wordt daarom zelf meegeleverd als `@font-face` in `app.css`
  (`.woff2`-bestanden onder `app/static/fonts/hack/`, MIT-licentie — zie `LICENSE.md` in die
  map). JetBrains Mono en Fira Code komen wél van Google Fonts, samen met de andere
  lettertypes in dezelfde `<link>` in `base.html`. Consolas is Microsoft-eigendom en kan niet
  meegeleverd worden — die keuze doet dus alleen iets als het lettertype al lokaal op het
  systeem van de bezoeker staat, anders valt de browser terug op de generieke `monospace`.
- **Swimlanes in-/uitklappen**: puur client-side (`app/static/js/kanban.js`), status per
  swimlane-id opgeslagen in `localStorage` onder een sleutel per bord-id — geen migratie of
  databaseveld nodig voor een enkele gebruiker. Hetzelfde `[hidden]`-i.c.m.-`display:flex`
  probleem als eerder bij `.pomodoro-controls`/`.notes-bulk-bar`: `.board-row[hidden]` moest
  expliciet `display: none` krijgen, anders wint `.board-row { display: flex }` van de
  standaard hidden-stijl.
- **Multi-tag filter op taken**: `GET /tasks?tags=werk&tags=prive` (herhaalde query-param,
  FastAPI's `Query(default=[])`) i.p.v. het vorige losse `tag`-param — de tasks-tabel wordt
  gefilterd met `Task.tags.any(Tag.name.in_(tags))` (OR-logica). De checkbox-lijst zelf toont
  alle tags die daadwerkelijk op een taak van de gebruiker staan (`Tag` gejoined via
  `Tag.tasks`), niet alle tags in het hele systeem (die kunnen ook van kanban/notities/
  snippets zijn). Quick-acties (afvinken, verwijderen) sturen de actieve filter-tags mee als
  herhaalde hidden inputs (`filter_tags`) zodat de weergave niet reset na de actie.
- **Taakgroepen in-/uitklappen**: zelfde patroon en zelfde `localStorage`-aanpak als de
  kanban-swimlanes, nu in `app/static/js/tasks-list.js`, met de groepsnaam zelf (niet de
  positie) als sleutel — blijft dus correct werken als de samenstelling van de groepen
  verandert door een andere filter.
- **Geen kleurtint meer op de taakrij**: `Task.row_tint_style` (achtergrondkleur van de hele
  rij, afgeleid van de eerste tag) is verwijderd. De tag-badges zelf blijven gekleurd
  (`Tag.badge_style`) — alleen de rij-brede tint is weg, op verzoek net iets rustiger en
  compacter (`.tasks-table th/td` heeft nu ook een eigen, kleinere padding dan de algemene
  tabel-stijl, en wordt in de compacte weergave nog verder verkleind).
- **Kalender**: `CalendarEvent` is een geheel losse entiteit (eigen tabel + `event_tags`,
  zelfde patroon als de andere taggable modellen) — een taak-deadline verschijnt wél in de
  kalender maar heeft daar geen eigen rij, puur een read-only weergave via een tweede query op
  `Task.deadline`. De maand-/weekgrid wordt berekend in `app/services/calendar_grid.py`
  (pure functies, apart getest): `month_weeks()` gebruikt `calendar.Calendar.monthdatescalendar`
  voor volle ma-zo-weken inclusief de dagen uit de vorige/volgende maand die de eerste/laatste
  week opvullen (die krijgen de CSS-klasse `calendar-day-other-month` i.p.v. weggelaten te
  worden). Maandnamen/dagnamen zijn hardcoded Nederlands (`DUTCH_MONTHS`/`DUTCH_WEEKDAYS`)
  i.p.v. `calendar.month_name` met een locale, want de container heeft geen Nederlandse
  locale ingesteld. Nieuwe/bewerkte afspraken gebruiken dezelfde eigen-pagina-aanpak als
  Taken/Notities/Snippets (`/calendar/events/new`, `?on=<datum>` vult de datum voor) i.p.v.
  een modal per dagcel, wat bij 35-42 cellen per maand een hoop overbodige HTML zou zijn.
- **Mini-kalender in de sidebar**: staat in `base.html` (dus op elke pagina) en wordt net als
  het "Komende deadlines"-widgetje via een kleine JSON-feed gevuld (`GET /calendar/widget`,
  `app/static/js/mini-calendar.js`) i.p.v. server-side in elke route te renderen. De rode
  stipjes komen uit `_marked_dates()` in `app/routers/calendar.py`: een simpele union van
  taak-deadlines en afspraak-datums in de zichtbare maand. Snel een taak aanmaken gaat via
  `POST /tasks/quick`, dat JSON teruggeeft in plaats van te redirecten — de widget staat op
  élke pagina (ook Kanban, Notities, ...) en mag de gebruiker dus niet wegnavigeren naar
  `/tasks` na het aanmaken. Na een geslaagde quick-add stuurt de widget een eigen
  `deadlines:refresh`-DOM-event, waar `deadlines.js` op luistert om zichzelf te verversen
  zonder dat beide widgets elkaar rechtstreeks hoeven te kennen.
