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
  (start met Backlog/Todo/In Progress/Done, per swimlane onafhankelijk uit te breiden) én een
  **accentkleur** op haar kolommen (net als tags — direct herkenbaar welke kolom bij welke
  swimlane hoort) — automatisch op naam toegewezen, maar met een kleine **kleurkiezer naast de
  swimlane-titel** ook zelf te overschrijven, drag-and-drop tussen kolommen binnen een swimlane,
  kaarten los van taken
- Kanban-kaarten zijn **bewerkbaar** (titel, beschrijving, tags) en kunnen een **accentkleur**
  krijgen (kleurenpicker, zichtbaar als gekleurde rand links op de kaart). Bewerken opent een
  **grotere, gecentreerde modal** (i.p.v. inline in de smalle kolom) met een **opmaak-werkbalk**
  (vet, cursief, kop, opsomming, code, en een link-knop die een URL + linktekst vraagt en er
  een klikbare markdown-link van maakt)
- Checklists in kaartbeschrijvingen (`- [ ] item`) — aanklikbaar, direct persistent; een
  "☑ Item"-knop op de werkbalk voegt de syntax voor je toe
- **Kale URL's worden automatisch klikbare links**, in taken-, kanban- en notitiebeschrijvingen —
  je hoeft geen `[tekst](url)`-syntax of de Link-knop te gebruiken; `www.mondschoon.nl`,
  `mondschoon.nl` en `https://mondschoon.nl/pagina` worden allemaal herkend zodra je ze plakt
  of typt, zolang ze niet al in een code-blok of bestaande link staan
  (`bleach.linkify`, toegepast na de markdown-rendering resp. bij het opslaan van een notitie)
- Gedeeld tag-systeem (taken + kanban-kaarten): elke tag krijgt automatisch een eigen,
  stabiele kleur; **sorteren** (deadline/titel/prioriteit/status) en **groeperen op tag**
  (dat is hier ook het "project"-alternatief — er is geen apart projectveld, tags dienen als
  project/categorie) op de takenlijst, met tag-groepen die je individueel kunt **in-/uitklappen**
  (status per groep onthouden in `localStorage`). **Filteren op tags** gaat via aanklikbare
  tag-checkboxes boven de lijst (meerdere tegelijk aan te vinken, OR-logica: een taak met
  minstens één van de aangevinkte tags blijft zichtbaar) — de taakrij zelf krijgt geen
  kleurtint meer op basis van de tag, alleen de tag-badge zelf is gekleurd
- Taken staan als **kaartjes** in de lijst (i.p.v. tabelrijen): een ronde afvink-cirkel
  links, vetgedrukte titel met de gekleurde tags eronder, deadline en status rechts in de
  meta-regel. De hele kaart is klikbaar om te bewerken (net als notities/snippets); de
  cirkel en de tags hebben hun eigen gedrag en negeren die klik. Een taak met een
  **prioriteitsvinkje** (★) krijgt een ster voor de titel en sorteert bovenaan de takenlijst;
  het **afvink-vinkje** zet de taak direct op "done" (doorgestreepte titel, gevulde cirkel) of
  terug naar "todo"; heeft de taak een beschrijving, dan staat er een **cursieve preview**
  (eerste 20 tekens) op de meta-regel. Tags en deadline staan **helemaal rechts** uitgelijnd
  op diezelfde regel (status en preview blijven links, direct na de titel)
- **Pomodoro-timer** als "Pomodoro"-menu-item in de sidebar i.p.v. een permanent zichtbaar
  blok: klik erop om een **grote, ronde, zwevende en verplaatsbare timer** rechtsonder in
  beeld te openen — een tomaatje, titel en tagline bovenin, de tijd groot in het midden met
  "van X min" eronder, **−5 min/+5 min-knoppen** om de werkduur snel bij te stellen, drie
  **preset-knoppen** (25/5/15 min) voor een directe keuze, en een grote ronde ▶/⏹-knop om te
  starten/stoppen. De voortgangsring eromheen gloeit oranje (rood tijdens een pauze) en loopt
  live leeg. Optioneel een taak koppelen via het (compacte) keuzemenu onderin. Het paneel
  blijft op zijn plek zolang je door de app navigeert, en verschijnt automatisch weer als er al
  een sessie loopt; sluiten via het kruisje stopt de timer niet, verbergt 'm alleen. Geschiedenis
  zichtbaar op de taakpagina. Een **"▶" focus-knop** op elke openstaande taak (in de
  takenlijst en op de bewerkpagina) opent het paneel meteen en **start direct een
  werk-sessie** voor die taak, zonder eerst zelf een taak of duur te hoeven kiezen
- 9 thema's: Dracula, One Dark Pro, Nord, Light (wit met oranje accenten), nexmail (graphite
  achtergrond met signaalgroen accent en het lettertype van nexmail — Space Grotesk voor
  koppen, IBM Plex Sans voor lopende tekst), macOS-Light (extra licht, clean/simpel thema
  naar macOS-stijl: zuiver wit met macOS-systeemblauw als accentkleur), **Anchor** en
  **Anchor Solid** (donker leigrijs/antraciet met een brandoranje accent — het kleurenpalet
  1-op-1 overgenomen van de night-mode van [zhfahim/anchor](https://github.com/zhfahim/anchor)
  op GitHub; Anchor Solid is de volledig ondoorzichtige variant), en **Wit** (in tegenstelling
  tot Light/macOS-Light is hier ook elke "verhoogde" laag — sidebar, kaarten — exact hetzelfde
  wit als de achtergrond, met een neutraal zwart accent; kaarten onderscheiden zich alleen via
  hun rand + zachte schaduw, voor een zo monochroom mogelijke, rustige look)
- **Apple-achtige vormtaal**, thema-onafhankelijk: de sidebar-navigatie heeft nu iconen in
  afgeronde vierkante badges, en de actieve pagina krijgt een gekleurde, volledig afgeronde
  "pil"-achtergrond (kleur volgt automatisch het actieve thema's accentkleur). Kaarten (taken,
  kanban, notities, snippets, statistieken, kalender-overzicht) hebben sterker afgeronde
  hoeken en een zachte schaduw i.p.v. een harde rand; knoppen en invoervelden zijn ook meer
  afgerond. Het Kanban-bord kreeg een kolomkop met een gekleurd bolletje + aantal-badge, en
  de "+ Kaart toevoegen"-knop is een neutrale pil-knop i.p.v. een kale link. De kolom zelf is
  bewust een **egaal, effen vlak** (geen kleurtint meer) — alleen het bolletje in de kolomkop
  en de rand van de swimlane-titel verraden nog welke swimlane een kaart bij hoort
- **Weergave-instellingen** (Account → Weergave): los van het thema kiesbaar **lettertype**
  (16 opties — systeemstandaard, de leesletters Inter/Roboto/Open Sans/Lato/Poppins/Nunito/
  Source Sans 3/Merriweather/Fira Sans/DM Sans, het sierlijke schreefletter Playfair Display,
  en de monospace/code-letters Hack/JetBrains Mono/Fira Code/Consolas), **lettergrootte**
  (13–18px) en **compactheid** (comfortabel/compact,
  verkleint de ruimte tussen tekst en elementen door de sidebar, tabellen, kaarten en formulieren).
  Ook een **achtergrondafbeelding** (Geen/Natuur/Bergen/Heelal, self-hosted foto's, geen
  externe API) met een **sterkte-schuifje** (10–70%) — de sidebar en het hoofdvlak worden dan
  semi-transparant zodat de foto erdoorheen schijnt, terwijl kaarten/tabellen zelf gewoon
  ondoorzichtig en leesbaar blijven
- Kanban-**swimlanes zijn in-/uitklapbaar**: klik op de swimlane-titel om de rij te verbergen.
  Status wordt per bord onthouden in `localStorage` (client-side, geen serverstate nodig voor
  een enkele gebruiker)
- **Notities**: lichte rich-text editor met knoppenbalk (vet, cursief, koppen, opsommingen,
  genummerde lijsten, links, code) — geen markdown-syntax typen nodig, wat je ziet is wat er
  opgeslagen wordt. Inhoud is HTML, server-side gesanitized (`bleach`) tegen XSS. Taggable met
  hetzelfde gedeelde tag-systeem als taken/kanban, met **aanklikbare tag-checkboxes** boven de
  lijst om op meerdere tags tegelijk te filteren (OR-logica) — de notitiekaart zelf krijgt
  geen kleurtint meer op basis van de tag, alleen de tag-badge is gekleurd. De hele kaart in de
  lijstweergave is klikbaar om te bewerken, en een **selectievak per notitie** maakt
  bulk-acties mogelijk: meerdere notities in één keer verwijderen of er samen een tag aan
  toevoegen. Een **"Tijdelijke notitie"-vinkje** markeert een notitie als **temp** (zichtbaar
  als badge in de lijst) — zo'n notitie wordt automatisch verwijderd zodra ze een week oud is.
- **Notities sorteren + raster-/lijstweergave**: een "Sorteren op"-keuzelijst (laatst
  gewijzigd / titel / aangemaakt, server-side, blijft staan bij tag-filteren en bulk-acties)
  en een **▦ Raster / ☰ Lijst-schakelaar** ernaast. Lijstweergave toont elke notitie als
  compacte rij (titel, tags, datum) i.p.v. een kaart — puur client-side CSS/JS (geen extra
  server-call), gekozen weergave onthouden in `localStorage` zodat ze blijft staan bij een
  volgend bezoek
  De notitiekaarten zelf zijn herontworpen naar de vormgeving van
  [zhfahim/anchor](https://github.com/zhfahim/anchor): sterk afgeronde hoeken, volledig
  ronde tag-pills met een "#"-prefix, en de datum onderaan de kaart
- **Code snippets** (ByteStash-stijl): een snippet kan **meerdere bestanden** bevatten (bv.
  `main.py` + `requirements.txt` bij elkaar), elk met een eigen taal voor **syntax
  highlighting** (highlight.js) — de taal wordt **automatisch afgeleid uit de
  bestandsextensie** zodra je een bestandsnaam typt (bv. `config.json` → json,
  `app.py` → python), en blijft daarna gewoon handmatig aan te passen via de select. Kaarten
  staan **in een raster** (net als notities) en **standaard ingeklapt** (alleen titel, tags en
  bestandsnamen) — klik erop om de code compact binnen die kaart te tonen, i.p.v. een regel
  die over het hele werkscherm uitrekt. Eén zoekveld doorzoekt titel, tag én code-inhoud
  tegelijk, taggable met hetzelfde gedeelde tag-systeem
- **Mindmap**: je kunt **meerdere, losse mindmaps aanmaken en opslaan** (net als notities of
  snippets, i.p.v. één vast bord) — de lijstpagina toont ze als **preview-kaarten** (net als
  notities): naam, **beschrijving**, aantal componenten en gekleurde **tags**, met
  **aanklikbare tag-checkboxes** erboven om op tag te filteren. Elke kaart heeft een
  "Bewerken"-uitklapper om naam/beschrijving/tags aan te passen zonder de mindmap te hoeven
  openen, en een verwijderknop. Een mindmap openen (bewerken) schakelt naar een **volledig
  scherm** (de sidebar verdwijnt, het canvas vult de hele pagina) met alleen een smalle
  bovenbalk (terug-link, naam bewerken, "+ Component"); teruggaan naar de lijst herstelt de
  normale weergave. Componenten hebben een **dunne rand** in hun eigen kleur en tonen
  standaard **alleen de tekst** — pas bij **dubbelklik** verschijnt de werkbalk (kleur
  wijzigen, verbonden component toevoegen, koppelen aan een ander component, verwijderen);
  een klik ernaast klapt 'm weer in. Componenten zijn vrij te **verslepen**; de
  **+**-knop maakt direct een nieuw, verbonden component aan (een idee uitwerken), de
  **🔗**-knop verbindt met een willekeurig bestaand component (twee losse steekwoorden aan
  elkaar binden, ook niet-hiërarchisch). Klik op een verbindingslijn om 'm te verwijderen
- **Kalender** (de **standaardpagina** na inloggen) met een **maand-** en **weekweergave**
  (te wisselen via de knoppen boven het rooster), navigatie met vorige/volgende en een
  "Vandaag"-knop, simpel/strak vormgegeven: één doorlopend raster met dunne lijnen tussen de
  dagen (geen losse "kaartjes" per dag), vandaag als een gekleurd rond bolletje om het
  dagnummer, en items als een klein gekleurd stipje + titel i.p.v. een gevulde badge. Toont
  twee soorten items door elkaar: **eigen afspraken** (titel, datum, beschrijving, tags — CRUD
  via `/calendar/events`, stipkleur volgt de eerste tag) en, puur ter info, **taken met een
  deadline** (klikbaar naar de taak, doorgestreept als de taak al "done" is, altijd een geel
  stipje). Elke dag heeft een "+"-knop (verschijnt bij hover) die direct een nieuwe afspraak
  opent met die datum vooringevuld. **Onder de kalender** staat een overzicht van wat er nu
  loopt: openstaande **hoge-prioriteitstaken**, de **3 meest recente notities** en de **3
  meest recente kanban-kaarten** — zo zie je in één oogopslag waar je mee bezig bent zonder
  naar elke pagina apart te navigeren
- **Mini-kalender in de sidebar**: een compact maandoverzicht op elke pagina, met een **rood
  stipje** op elke dag die een taak-deadline of afspraak heeft. Klik op een dag om direct
  (zonder de pagina te verlaten) een **taak aan te maken met die dag als deadline** — verschijnt
  meteen in de takenlijst en het "Komende deadlines"-widgetje. De maandnaam bovenin is ook een
  link naar de volledige kalenderpagina (maand-/weekweergave)
- **API voor externe agents/scripts** (Account → API-token): een los token (los van je
  wachtwoord, `Authorization: Bearer <token>`-header) waarmee een extern script taken,
  kanban-kaarten, notities en code-snippets kan aanmaken via `/api/v1/tasks`,
  `/api/v1/kanban/cards`, `/api/v1/notes` en `/api/v1/snippets` (JSON in, JSON uit). Een
  kanban-kaart aanmaken zonder swimlane/kolom op te geven belandt automatisch in de eerste
  kolom van de eerste swimlane. Het token wordt maar één keer getoond (alleen de hash wordt
  bewaard) en is op elk moment in te trekken
- **Backup** (Account → Backup): de hele database (taken, kanban, notities, snippets,
  kalender, mindmap, instellingen) in één keer **exporteren** als downloadbaar `.db`-bestand,
  en later weer **importeren** om alles terug te zetten — er wordt automatisch eerst een
  veiligheidskopie van de huidige database gemaakt voordat 'm vervangen wordt
- **Quick-add-wiel**: een ronde hub-knop rechtsonder (op elke pagina, met een 4-stippen-icoon)
  die bij een klik openklapt naar een **semi-transparant rond menu** met 5 taartpunten —
  **Notities**, **Kanban**, **Snippets**, **Taken** en **Mindmap** — elk met een eigen icoon en
  label, die direct doorlinken naar de bijbehorende aanmaakpagina (`/notes/new`, `/kanban`,
  `/snippets/new`, `/tasks/new`, `/mindmap`). Klik ergens buiten het wiel of druk op Escape om
  het weer te sluiten
- **Bredere, gecentreerde aanmaak-/bewerkpagina's**: de formulieren voor taken, notities en
  snippets staan in een gecentreerde kolom (i.p.v. links tegen de sidebar aan) met merkbaar
  grotere invoervelden, zodat er meer leesbaar is tijdens het invullen op een groot scherm. De
  kanban-kaart-modal is om dezelfde reden ook iets breder geworden
- **Statistieken-pagina** (menu-item "Statistieken", `/stats`): een reeks tegels met simpele
  productiviteitscijfers — afgeronde taken (en percentage), openstaande
  hoge-prioriteitstaken, gehaalde deadlines, openstaande verlopen deadlines, aantal
  gestarte/voltooide pomodoro's, totale focustijd, en nieuwe taken/kanban-kaarten/notities
  per week en per maand — plus **gekleurde balkgrafieken** — focustijd per dag (laatste 14 dagen) en per maand
  (laatste 6 maanden, met een berekend gemiddelde focustijd per dag deze maand), plus
  **aangemaakt vs. afgerond** (taken + notities + kanban-kaarten aangemaakt, taken afgerond)
  als gegroepeerde balken per dag/week/maand. Elke grafiek toont ook een **gestippelde
  gemiddelde-lijn** op dezelfde schaal als de balken (bij de gegroepeerde grafieken één lijn
  per reeks, met het exacte gemiddelde in de legenda zodat de labels nooit over elkaar heen
  vallen ook als beide gemiddeldes dicht bij elkaar liggen). Puur CSS-balken met een
  server-berekend percentage t.o.v. de hoogste waarde in de reeks
  (`app/services/stats.py::compute_activity_charts`) — geen chart-library nodig, in lijn met
  de rest van de app
- **Graph** (nieuw menu-item "Graph"): een interactieve, sleepbare **taggraaf** — net als de
  graph-view in Obsidian, maar dan getagde taken/notities/kanban-kaarten/mindmaps die
  gegroepeerd worden rond de tags die ze delen. Kleur per type (taak/notitie/kanban/mindmap/
  tag), klik op een item om het direct te openen, sleep een knooppunt om de layout aan te
  passen. Items zonder tags verschijnen niet in de graaf (ze kunnen met niets linken)
- **Mobiel-geoptimaliseerd**: onder 768px breedte (telefoon) verandert de sidebar in een
  **inklapbaar off-canvas menu** — een hamburgerknop linksboven opent het als paneel over de
  inhoud heen (met achtergrond-overlay, sluit bij een tik ernaast, Escape of het kiezen van
  een menu-item). De hoofdinhoud wordt volle breedte, de Pomodoro-cirkel en het quick-add-wiel
  worden kleiner zodat ze op een smal scherm passen, en Kanban-kolommen zijn smaller zodat je
  makkelijker van kolom naar kolom kunt swipen
- **Voice-notitie (fase 1: opnemen → transcriberen → opslaan)**: een nieuwe 🎤 "Voice"-spaak
  in het quick-add-wiel opent een opnamepaneel. Opname gebeurt in de browser
  (`MediaRecorder`), het audiofragment gaat naar `POST /voice/transcribe`, dat het
  doorstuurt naar een **losse, zelf-gehoste Whisper-container** (bv.
  `ahmetoner/whisper-asr-webservice`, zie Configuratie hieronder) voor de transcriptie. Je
  ziet en corrigeert het transcript zelf vóórdat je op "Opslaan als notitie" klikt — dat
  is bewust de bevestigingsstap, want spraakherkenning gaat af en toe mis. Fase 2 (nog niet
  gebouwd): ChatGPT laten interpreteren of het transcript een taak/kanban-kaart/notitie
  moet worden i.p.v. altijd een notitie, met een eigen bevestigingsscherm — de
  OpenAI-sleutel daarvoor kun je nu alvast instellen via Account → OpenAI API-sleutel, met
  een **"Sleutel testen"-knop** die de zojuist ingevulde (nog niet per se opgeslagen)
  sleutel direct tegen `GET https://api.openai.com/v1/models` test en meldt of 'm werkt —
  zonder dat je eerst hoeft op te slaan of ergens anders hoeft te controleren

Nog niet gebouwd: CI/CD, slimme voice-commando-interpretatie (taak/kanban/notitie kiezen +
matchen op bestaande items via ChatGPT — de basis "opnemen → transcriberen → als notitie
opslaan" werkt al, zie hierboven), verdere LLM-koppeling (er is nu wel een API voor
scripts/agents, zie hieronder).

## Configuratie

Geen `.env`-bestand of omgevingsvariabelen nodig. Bij de eerste start:
- wordt een sessie-secret-key automatisch gegenereerd en opgeslagen in `data/.secret_key`
  (blijft geldig na herstarts/updates, zolang het data-volume bewaard blijft);
- wordt een seed-account aangemaakt: gebruikersnaam `admin`, wachtwoord `admin`.

Voor voice-notities heb je een **losse Whisper-container** nodig (draait niet mee in de
hoofd-image, zie architectuur hieronder). Zet de env var `WHISPER_SERVICE_URL` op de URL
van die container (default: `http://whisper:9000`). Voorbeeld met de webservice van het
[`ahmetoner/whisper-asr-webservice`](https://github.com/ahmetoner/whisper-asr-webservice)-project
(Docker Hub-image heet `onerahmet/openai-whisper-asr-webservice`, andere naam dan de
GitHub-repo):

```bash
docker run -d --name whisper -p 9000:9000 \
  -e ASR_MODEL=base \
  onerahmet/openai-whisper-asr-webservice:latest
```

Zonder deze container werkt de rest van de app gewoon door — je krijgt dan alleen een
duidelijke foutmelding zodra je een voice-notitie probeert op te nemen.

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
   "Komende deadlines"-widgetje in de sidebar. Klik ergens op de taakkaart (niet de cirkel of
   een tag) → opent de bewerkpagina.
3. Taak bewerken en status wijzigen naar "done". Op de takenlijst de ronde afvink-cirkel
   gebruiken → status wisselt direct tussen "todo" en "done" (cirkel vult zich, titel wordt
   doorgestreept), en de huidige sortering/groepering/filter blijft daarbij behouden (ook na
   filteren op status/tag).
4. Taken aanmaken met verschillende tags → controleer dat elke tag een eigen kleur heeft en
   dat de taakkaart zelf geen kleurtint krijgt (alleen de tag-badge is gekleurd). Meerdere
   tag-checkboxes boven de lijst aanvinken → filtert op taken met minstens één van die tags.
   Sorteren op titel/prioriteit/status en groeperen op tag uitproberen, en een tag-groep
   in-/uitklappen (herlaad de pagina en controleer dat de klap-status bewaard is gebleven).
5. Naar Kanban gaan, een swimlane toevoegen (krijgt automatisch eigen Backlog/Todo/In Progress/Done)
   en daar een eigen kolom aan toevoegen → controleer dat die kolom alleen in díe swimlane
   verschijnt. Klik op het kleurbolletje naast de swimlane-titel en kies een kleur → controleer
   dat de kolomkopjes en de linkerrand van de titel direct meekleuren (geen page reload nodig)
   en dat de kleur bewaard blijft na herladen. Een kaart aanmaken met een checklist (`- [ ] item`) → klik een checklist-item
   aan en herlaad de pagina om te controleren dat het aangevinkt blijft. Klik "Bewerken" op
   een kaart → een grotere, gecentreerde modal opent met een opmaak-werkbalk. Selecteer tekst
   en klik Vet/Cursief, en probeer de Link-knop (vraagt om een URL) → controleer na opslaan
   dat de kaart een klikbare link toont. Geef de kaart ook een titel/kleur/tags en controleer
   dat de gekleurde rand verschijnt en blijft na herladen. Klik op de achtergrond (backdrop)
   of "Annuleren" om de modal te sluiten zonder op te slaan.
6. Kaart verslepen naar een andere kolom/swimlane (drag-and-drop) → herlaad de pagina en
   controleer dat de cel-toewijzing bewaard is gebleven.
7. Klik op "Pomodoro" in de sidebar → de grote ronde timer opent rechtsonder. Sleep 'm aan het
   bovenste deel (icoon/titel) naar een andere plek. Klik "+"/"−" of een preset (25/5/15 min)
   om de werkduur te wijzigen → de tijd en "van X min" passen meteen aan. Start de timer
   (kies eventueel een taak in het keuzemenu onderin) → controleer dat de ring vol en
   gloeiend oranje wordt, de aanpasknoppen/presets uitgeschakeld raken, en de knop in het
   midden een stopknop (rood vierkant) wordt. Controleer de automatische overgang naar de
   pauze-fase (ring wordt groen), en dat navigeren naar een andere pagina het paneel op
   dezelfde plek en met de lopende timer laat staan. Sluit het paneel via het kruisje en open
   het opnieuw via het menu → de timer loopt gewoon door. Controleer op de taakpagina dat
   voltooide werk-sessies meetellen in de Pomodoro-historie.
8. Thema wisselen via de kleurenbolletjes in de sidebar (incl. het lichte thema) → voorkeur
   blijft na herladen/opnieuw inloggen behouden.
9. Naar Notities gaan, een notitie aanmaken: tekst selecteren en vet/cursief maken via de
   knoppenbalk, een kop toepassen, een lijst en een link toevoegen, plus tags → controleer dat
   de kaart in de lijstweergave de opmaak en gekleurde tags toont (elke tag een andere, bij
   aanmaak willekeurig gekozen kleur), en dat de kaart zelf géén kleurtint krijgt (alleen de
   tag-badge is gekleurd). Meerdere tag-checkboxes boven de lijst aanvinken → filtert op
   notities met minstens één van die tags. Klik ergens op een kaart (niet alleen de titel) →
   opent de bewerkpagina. Vink twee notities aan via het selectievakje → de bulk-balk
   verschijnt bovenaan; voeg een tag toe aan de selectie en controleer dat beide notities 'm
   krijgen zonder bestaande tags te verliezen, en test daarna bulk-verwijderen. Maak een
   notitie aan met "Tijdelijke notitie" aangevinkt → de kaart in de lijst toont een
   "TEMP"-badge (deze wordt pas na een week automatisch verwijderd, bij een bezoek aan de
   notitielijst).
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
13. Bij Account → Weergave een achtergrond kiezen (bv. Bergen) en het sterkte-schuifje
    aanpassen → sidebar en hoofdvlak worden semi-transparant met de foto erdoorheen, kaarten
    en tabellen blijven zelf gewoon leesbaar/ondoorzichtig. Zet 'm terug op "Geen" → normale
    weergave terug zonder foto.
14. Naar Mindmap gaan → geef een naam op en klik "+ Nieuwe mindmap" → opent de editor in
    **volledig scherm** (sidebar verdwijnt), met één "Hoofdonderwerp"-component (dunne rand,
    alleen tekst zichtbaar). Dubbelklik het component → de werkbalk (kleur/+/🔗/×) verschijnt;
    klik ernaast → werkbalk klapt weer in. Sleep het component naar een andere plek, herlaad
    en controleer dat de positie bewaard is. Dubbelklik weer, klik "+" om een verbonden
    component toe te voegen, wijzig de kleur en de tekst (klik erin, typ, klik ernaast om op
    te slaan). Maak nog een los component via "+ Component" boven de pagina, dubbelklik het
    eerste component, klik 🔗 en dan op het losse component om ze te verbinden. Klik op een
    verbindingslijn om 'm te verwijderen, en verwijder een component via × → de bijbehorende
    verbindingen verdwijnen mee. Klik "← Mindmaps" → normale weergave (met sidebar) is terug,
    en de mindmap staat in de lijst met naam en aantal componenten; hernoem 'm door de naam
    bovenin te wijzigen, en verwijder 'm via de lijst.
15. Bij Account → API-token op "Token genereren" klikken → het token wordt één keer getoond.
    Test 'm vanaf de terminal, bv.:
    ```bash
    curl -X POST http://localhost:8887/api/v1/tasks \
      -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
      -d '{"title": "Taak via API", "tags": "agent"}'
    ```
    → controleer dat de taak verschijnt op `/tasks`. Probeer hetzelfde met
    `/api/v1/kanban/cards`, `/api/v1/notes` en `/api/v1/snippets`. Klik daarna "Intrekken" →
    hetzelfde token geeft nu een 401.
16. Bij Account → Backup op "Database exporteren" klikken → een `.db`-bestand wordt
    gedownload. Maak een testtaak aan, importeer daarna het zojuist gedownloade bestand terug
    (met de bevestiging) → je wordt naar de inlogpagina gestuurd; na opnieuw inloggen is de
    testtaak weer weg (en staat er een `app.db.before-import-<tijdstip>`-veiligheidskopie in
    de `data`-map).
17. Uitloggen en controleren dat alle pagina's terug naar `/login` sturen.
18. Rechtsonder (op elke pagina) staat een ronde knop met vier stippen → klik erop → een
    semi-transparant rond menu met 5 taartpunten (Notities/Kanban/Snippets/Taken/Mindmap)
    klapt open. Klik op "Taken" → je komt op `/tasks/new`. Ga terug, open het wiel opnieuw en
    klik op "Kanban" → `/kanban` (de bordpagina). Herhaal voor "Snippets" (`/snippets/new`),
    "Notities" (`/notes/new`) en "Mindmap" (`/mindmap`). Open het wiel en klik ergens buiten
    het wiel (of druk Escape) → het sluit weer zonder te navigeren.
19. Log opnieuw in (of ga naar `/`) → je komt nu op de Kalender terecht i.p.v. Taken. Maak een
    taak aan met prioriteit aangevinkt, een notitie en een kanban-kaart → ga naar de Kalender
    en controleer dat alle drie verschijnen in het overzicht onder het rooster ("Hoge
    prioriteit", "Recente notities", "Recente kanban-kaarten"). Vink de hoge-prioriteitstaak af
    → ze verdwijnt uit dat overzicht.
20. Op een taakkaart in de takenlijst (en op de bewerkpagina van een taak) staat een "▶"-knop
    → klik erop → het Pomodoro-paneel opent rechtsonder en start meteen een werk-sessie voor
    die taak (controleer via de taakbewerkpagina dat de Pomodoro-historie deze sessie meetelt
    zodra ze afloopt/voltooid is). Probeer de knop nogmaals te klikken terwijl er al een sessie
    loopt → een melding zegt dat je eerst de lopende sessie moet stoppen.
21. Ga naar "Statistieken" in de sidebar (`/stats`) → tegels voor afgeronde taken, hoge
    prioriteit, gehaalde/verlopen deadlines, gestarte/voltooide pomodoro's, focustijd, en
    nieuwe taken/kanban-kaarten/notities per week en maand. Start een pomodoro-sessie en
    herlaad de pagina → "Pomodoro's opgestart" telt méé. Controleer ook dat Account/Settings
    zelf geen statistieken-sectie meer toont (die is hierheen verplaatst).
22. Kies het "Anchor"-thema via de kleurenbolletjes in de sidebar → donker leigrijs met een
    brandoranje accent. Ga naar Notities → de kaarten zijn sterk afgerond, tags staan als
    volledig ronde pilletjes met een "#"-prefix, en onderaan elke kaart staat de datum. Ga
    naar Account → Weergave → Lettertype en kies "Playfair Display" → koppen/titels tonen nu
    in een sierlijke schreefletter; kies "DM Sans" voor de bijpassende leesletter.
23. Geef een taak, een notitie, een kanban-kaart én een mindmap dezelfde tag (bv. "test") →
    ga naar "Graph" in de sidebar → er verschijnt een grote grijze tag-knoop "#test" met vier
    gekleurde knooppunten eromheen (één per type, zie de legenda bovenaan). Sleep een
    knooppunt → het blijft op die plek terwijl de rest zich eromheen herschikt. Klik op een
    item-knooppunt (niet de tag zelf) → je komt op de bewerkpagina van dat item.
24. Verklein het browservenster (of open op een telefoon) tot onder ~768px breed → de sidebar
    verdwijnt en een hamburgerknop (☰) verschijnt linksboven. Klik erop → de sidebar klapt
    open als paneel met een donkere overlay erachter. Klik op een menu-item → je navigeert
    ernaartoe én het paneel klapt vanzelf weer dicht. Open het opnieuw en tik op de overlay
    (naast het paneel) → het sluit zonder te navigeren. Controleer op Kanban dat de kolommen
    smaller zijn en je horizontaal kunt scrollen, en dat de Pomodoro-cirkel en het
    quick-add-wiel volledig binnen het scherm passen.
25. Maak een paar taken aan en rond er één af, start en voltooi een Pomodoro-sessie → ga naar
    "Statistieken" in de sidebar (`/stats`). Controleer dat de tegels bovenaan kloppen
    (focustijd, gemiddelde per dag deze maand, afgeronde taken), dat de vandaag-kolom in
    "Focustijd per dag" en in "Aangemaakt vs. afgerond — per dag" een balk toont, en dat de
    balken in de week-/maandgrafieken meetellen in de juiste periode. Beweeg de muis over een
    balk → een tooltip met het exacte aantal verschijnt. Controleer dat elke grafiek een
    gestippelde gemiddelde-lijn toont (bij "Focustijd" één lijn met een "Gem. ..."-label erop,
    bij "Aangemaakt vs. afgerond" twee lijnen — de exacte gemiddeldes staan in de legenda
    erboven i.p.v. als label op de lijn, zodat ze nooit overlappen als beide gemiddeldes
    dicht bij elkaar liggen).
26. Typ in een notitie, een taakbeschrijving én een kanban-kaartbeschrijving een kale URL
    zonder markdown-syntax, bv. "zie www.mondschoon.nl voor info" → sla op en controleer dat
    de URL overal automatisch een klikbare link is geworden (blauw/onderstreept al naar gelang
    het thema), zonder dat je de Link-knop of `[tekst](url)` hoefde te gebruiken. Zet dezelfde
    URL ook even tussen backticks (\`www.mondschoon.nl\`) in een taakbeschrijving → controleer
    dat die in de preview gewoon platte code-tekst blijft (niet gelinkt).
27. Klik op het quick-add-wiel op de nieuwe 🎤 "Voice"-spaak → een opnamepaneel opent. Zonder
    een draaiende Whisper-container: druk op opnemen, spreek iets in, druk nogmaals om te
    stoppen → na even wachten verschijnt een duidelijke foutmelding ("Kan de Whisper-service
    niet bereiken..."). Start daarna een Whisper-container (zie Configuratie hierboven) en
    herhaal de opname → het transcript verschijnt in een bewerkbaar tekstvak met een
    voorgestelde titel. Pas het eventueel aan en klik "Opslaan als notitie" → je komt op de
    notities-pagina en de nieuwe notitie staat er met het (aangepaste) transcript in.
28. Ga naar Account → OpenAI API-sleutel. Klik "Sleutel testen" zonder iets in te vullen →
    "Vul eerst een sleutel in." verschijnt in rood. Typ een willekeurige/onechte sleutel
    (bv. "sk-test") en klik nogmaals → na een korte call naar de echte OpenAI API verschijnt
    "Ongeldige sleutel (401 Unauthorized)." Vul je eigen echte OpenAI-sleutel in en test
    opnieuw → "Sleutel werkt." in groen. Sla de sleutel op en controleer dat "Sleutel
    testen" ook zonder iets in het veld te typen werkt (test dan de al-opgeslagen sleutel).
29. Maak een paar notities aan met duidelijk verschillende titels → ga naar Notities en klik
    "☰ Lijst" → de kaarten worden compacte rijen (titel, tags, datum). Herlaad de pagina →
    de lijstweergave blijft staan (localStorage). Kies bij "Sorteren op" → "Titel" →
    controleer dat de notities alfabetisch gesorteerd staan, ook nog in lijstweergave. Vink
    een tag aan om te filteren → de sortering blijft "Titel". Klik terug naar "▦ Raster" →
    de kaartweergave komt terug.

## Architectuur

- **Backend**: FastAPI (async-vriendelijk, ingebouwde validatie/docs) + SQLAlchemy 2.0 ORM
  (zodat een latere Postgres-migratie mogelijk blijft zonder dat we er nu voor bouwen).
- **Frontend**: Server-rendered Jinja2 templates, progressive enhancement met vanilla JS
  (drag-and-drop) en Alpine/HTMX-ready (HTMX is al ingeladen voor latere fasen).
- **Auth**: Sessie-cookie met `itsdangerous`, wachtwoord-hashing via `passlib[bcrypt]`.
- **Graph-view** (`app/routers/graph.py`, `app/static/js/graph.js`): een **bipartiete
  taggraaf** i.p.v. losse item-naar-item-links — dit project heeft geen `[[wiki-links]]`
  tussen items, dus is de natuurlijke vertaling van "items met dezelfde tag linken" een
  knooppunt per tag waar elk getagd item een edge naartoe krijgt (`GET /graph/data` bouwt dit
  simpelweg op met vier losse queries — taken/notities/kanban-kaarten/mindmaps — en een
  `tag_node()`-helper die per tag-id maar één knooppunt aanmaakt). De layout is een simpele,
  **dependency-vrije force-directed simulatie op canvas 2D** (afstoting tussen alle
  knooppuntparen, aantrekking langs edges naar een gewenste lengte, een zachte trek naar het
  midden) i.p.v. een library als D3/vis.js erbij te halen voor één simpel view — dat paste
  niet bij hoe minimalistisch de rest van de front-end is opgezet. Items zonder tags worden
  serverside al overgeslagen (ze kunnen toch met niets linken), dus de graaf blijft klein
  genoeg voor de O(n²)-afstotingsberekening.
- **Mobiel navigatiemenu** (`.mobile-menu-btn`/`.sidebar-backdrop` in `base.html`,
  `app/static/js/mobile-nav.js`, `@media (max-width: 768px)` in `app.css`): een off-canvas
  sidebar (`transform: translateX(-100%)` → `translateX(0)` bij `.mobile-open`) i.p.v. een
  responsive herindeling van de bestaande layout — de sidebar-inhoud (mini-kalender,
  deadlines, thema-kiezer) is best breed en zou een herschikte inline-navigatie op een
  telefoonscherm onleesbaar maken. Dit was de **eerste responsive/mobiele CSS in de hele
  app** (voorheen geen enkele `@media`-query) — bewust in één media-query-blok onderaan
  `app.css` gehouden i.p.v. verspreid door het bestand, zodat het overzichtelijk blijft wat
  er specifiek voor mobiel anders is. De sidebar sluit zichzelf bij het klikken op een link
  of formulier-knop erin (bv. een thema kiezen), zodat je na een navigatie niet alsnog het
  paneel handmatig hoeft dicht te tikken.
- **Cache-busting voor statische bestanden** (`app/templating.py`, `static_url()`): elke
  `<link>`/`<script>` naar `/static/css/...` of `/static/js/...` gaat via
  `{{ static_url('pad') }}`, dat er een `?v=<bestand-mtime>` achteraan plakt. Zonder dit bleven
  browsers na een update soms een oude `app.css`/`pomodoro.js` cachen totdat iemand handmatig
  de cache leegde — met dit systeem verandert de URL vanzelf zodra een bestand wijzigt (nieuwe
  Docker-image = nieuwe mtimes = nieuwe URL's), dus geen harde refresh meer nodig na
  `install-unraid.sh`.
- **Kanban-kaarten** zijn losse entiteiten (geen 1-op-1 met Taken) — een kaart kan optioneel
  naar een taak verwijzen, maar dat is geen vereiste.
- **Swimlanes en kolommen**: `KanbanColumn` hangt aan een `KanbanSwimlane` (niet meer direct
  aan het bord), zodat elke swimlane haar eigen kolommenset heeft. Een nieuwe swimlane krijgt
  automatisch de standaardkolommen (Backlog/Todo/In Progress/Done) mee als startpunt, daarna volledig
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
- **Swimlane-kleuren zijn handmatig instelbaar, met een naam-gebaseerde fallback**: elke
  swimlane heeft een optioneel `color`-veld (kleine kleurkiezer naast de swimlane-titel,
  direct opgeslagen via `POST /kanban/swimlanes/{id}/color`, geen page reload nodig). Zolang
  er geen kleur is gekozen valt `KanbanSwimlane.display_color` terug op
  `app/services/colors.py::stable_hue()` — een hash-gebaseerde tint puur berekend uit de
  swimlane-naam, zodat een nieuwe swimlane toch meteen een herkenbare, stabiele kleur heeft
  (bv. na het per ongeluk verwijderen en opnieuw aanmaken van een swimlane).
- Rijtinten en kolomaccenten gebruiken telkens een transparante hsla-laag i.p.v. een vaste
  licht/donker kleur, zodat ze in elk thema goed leesbaar blijven.
- **Groeperen op tag**: een taak met meerdere tags verschijnt in elke bijbehorende groep
  (geen kunstmatige keuze voor "de hoofdtag"); taken zonder tag komen in een aparte
  "Zonder tag"-groep aan het eind.
- **Taken als kaartjes i.p.v. tabelrijen**: de takenlijst gebruikte eerst een `<table>` per
  groep met vaste kolombreedtes (`table-layout: fixed` + `<colgroup>`) om uitlijning tussen
  filters/groepen te garanderen. Dat probleem bestaat niet meer sinds elke taak een losse
  `.task-card`-`<div>` is (geen kolommen om uit te lijnen) — de kaarten staan in een simpele
  `.task-card-list` (flex-column), met dezelfde `data-group-block`/`data-group-toggle`-aanpak
  als de kanban-swimlanes voor het in-/uitklappen van tag-groepen.
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
- **Taakkaart-preview i.p.v. deadline-gradiëntbalk**: de eerdere kleurverloop-balk
  (`Task.urgency_color`, antraciet → donkeroranje) is verwijderd — in plaats daarvan toont de
  meta-regel, als de taak een beschrijving heeft, de eerste 20 tekens cursief
  (`task.description[:20]`), zodat je zonder de kaart open te klikken al een idee hebt
  waar de taak over gaat.
- **Tijdelijke notities** (`Note.is_temp`): er is bewust geen scheduler/cron in deze
  self-hosted app opgetuigd voor één simpele opruimtaak. In plaats daarvan ruimt
  `_delete_expired_temp_notes()` in `app/routers/notes.py` verlopen temp-notities
  (`created_at` ouder dan `TEMP_NOTE_LIFETIME` = 7 dagen) op **opportunistisch**, bij elk
  bezoek aan `GET /notes` — die pagina wordt vaak genoeg bezocht om verlopen notities snel te
  laten verdwijnen zonder een apart achtergrondproces.
- **Bredere, gecentreerde formulieren** (`.form-page` in `app/static/css/app.css`): een
  gedeelde wrapper-class (max-breedte 720px, `margin:0 auto`) om de taken-, notitie- en
  snippet-formulieren, i.p.v. de eerdere losse inline `style="max-width:...px"` per veld.
  Grotere `padding`/`font-size` op inputs/textareas is ook via die class gescoped, zodat het
  de rest van de app (bv. kleine tag-filters) niet raakt. De kanban-kaart-modal was al
  gecentreerd via `position:fixed` + `transform:translate(-50%,-50%)`, dus die kreeg alleen
  een iets bredere `width` en grotere invoervelden.
- **Kalender als standaardpagina + overzicht** (`app/routers/calendar.py`): `GET /` redirect
  nu naar `/calendar` i.p.v. `/tasks`. `_overview()` haalt drie kleine lijstjes op (top 3 per
  categorie, geen paginering) — hoge-prioriteitstaken (`priority=True`, niet "done"), de 3
  meest recent bijgewerkte notities, en de 3 meest recent aangemaakte kanban-kaarten (via een
  join op `KanbanBoard.user_id`, want `KanbanCard` heeft geen eigen `user_id`-kolom).
- **Pomodoro starten vanaf een taak**: de bestaande `#pomodoro-task`-keuzelijst en
  `startPhase()`-functie in `pomodoro.js` bleken al precies te doen wat nodig was — er is dus
  geen nieuw backend-endpoint bijgekomen. Een `.pomodoro-focus-btn` (met `data-task-id`) op de
  taakkaart en de bewerkpagina dispatcht via event-delegation (`document.addEventListener`
  op `.pomodoro-focus-btn`) meteen een `startPhase("work", ...)`-aanroep met die taak, i.p.v.
  eerst het paneel te openen en de taak handmatig uit de keuzelijst te kiezen. Loopt er al een
  sessie, dan waarschuwt een `alert()` i.p.v. de lopende sessie stilzwijgend te vervangen.
- **Statistieken** (`app/services/stats.py`, `compute_user_stats()`): bewust query-based
  (COUNT/SUM in SQL) i.p.v. Python-side loops over alle taken/kaarten/notities, zodat dit ook
  bij veel data snel blijft. "Behaalde deadline" heeft geen eigen "voltooid op"-veld nodig —
  `updated_at` (dat al bijwerkt bij het afvinken) dient als proxy: gehaald = afgerond met
  `updated_at`-datum op of vóór de deadline.
- **Anchor-thema en notitiekaart-restyling**: het kleurenpalet (`app/static/css/themes/anchor.css`)
  is letterlijk overgenomen uit `web/app/globals.css` (het `.dark`-blok) van
  [zhfahim/anchor](https://github.com/zhfahim/anchor) — dezelfde variabelenamen bestonden al
  in dit project (`--bg`, `--bg-elevated`, `--accent`, ...), dus was het een kwestie van de
  hex-waarden 1-op-1 overnemen i.p.v. zelf iets na te bootsen. `--success`/`--warning`/`--link`
  stonden niet in hun palet (zij gebruiken alleen accent/destructive) en zijn zelf gekozen in
  dezelfde "Deep Ocean & Sand"-sfeer. DM Sans, Playfair Display en JetBrains Mono zijn hun
  daadwerkelijke fonts (uit `web/app/layout.tsx`, via `next/font/google`) — JetBrains Mono
  stond al in de lettertype-lijst, DM Sans en Playfair Display zijn toegevoegd. De
  notitiekaart-CSS (`.note-card`, `.note-card-tags .tag`) is losstaand van het thema: die
  vormgeving (afronding, tag-pills, datum) geldt in elk thema, de kleuren komen gewoon uit de
  bestaande `--bg-elevated`/`--accent`-variabelen van welk thema er ook actief is.
- **Grote ronde Pomodoro-timer**: dezelfde server-kant (`/pomodoro/...`, één sessie per keer,
  client-side countdown) is ongewijzigd — alleen de front-end (`.pomodoro-float` in
  `app/templates/base.html`, `app/static/js/pomodoro.js`) is herbouwd naar een cirkel i.p.v.
  een klein rechthoekig paneel. De losse werk-/pauze-minuten-`<input>`'s zijn vervangen door
  drie preset-knoppen (25/5/15 min) plus −5/+5-stapknoppen; er is geen apart "Start"/"Stop"-
  knoppenpaar meer, maar één `#pomodoro-toggle-btn` die van icoon/kleur wisselt. De
  ring-dashoffset-berekening (`CIRCUMFERENCE`, `stroke-dasharray`/`-dashoffset`) is exact
  hetzelfde gebleven, alleen `RADIUS` is groter (26 → 90) voor de grotere cirkel.
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
- **Quick-add-wiel**: `.quickadd-wheel-wrap` in `base.html` + `app/static/js/quickadd.js`.
  De 5 snelkoppelingen zijn gewone `<a>`-links (geen los `/quick`-formulier meer, na eerdere
  iteraties die dat wel hadden) — het enige JS is het open/dicht togglen van het wiel. De
  taartpunt-kleuren komen uit één `conic-gradient` (5 gelijke segmenten van 20%, gestart op
  `-36deg` zodat de segmentgrenzen tussen de iconen vallen i.p.v. er middenin), i.p.v. 5 losse
  gestileerde `<div>`'s. Elke `.quickadd-spoke` staat gepositioneerd via een vooraf berekende
  `translate(x, y)` (trigonometrie op 72°-intervallen, radius 100px vanuit het midden) i.p.v.
  `sin()`/`cos()` in CSS, voor bredere browserondersteuning. `.quickadd-wheel-wrap` is 64×64px
  als het wiel dicht is (hub plakt in de hoek) en 300×300px als het open is — de hub zelf is
  altijd gecentreerd in die wrapper (`top:50%;left:50%;transform:translate(-50%,-50%)`), dus
  schuift vanzelf mee van de hoek naar het midden van het opengeklapte wiel, zonder dat de hub
  zelf een aparte positie-berekening nodig heeft. `app/services/kanban_cells.py` (met
  `get_or_create_default_cell`, gedeeld met de agent-API in `app/routers/api.py`) staat hier
  los van en is gewoon blijven staan.
- **Apple-achtige vormtaal**: bewust géén nieuw thema of losse "Apple-modus", maar een
  uitbreiding van de bestaande gedeelde classes (`.nav-item`, `.task-card`, `.note-card`,
  `.kanban-card`, `.column`, `.btn`, inputs) zodat elk van de 8 thema's er automatisch mooier
  uitziet zonder dat er 8× apart iets aangepast moest worden — alleen `border-radius` en
  `box-shadow` (geen harde `border` meer op de meeste kaarten) zijn breder toegepast, de
  thema-kleurvariabelen (`--bg-elevated`, `--accent`, ...) blijven de enige plek waar kleur
  vandaan komt. De sidebar-navigatie is verbouwd van losse `.sidebar a`-links naar één
  `.nav-item`-class met een `.nav-icon`-badge; de actieve pil-achtergrond gebruikt
  `color-mix(in srgb, var(--accent) 16%, transparent)` voor een subtiele, thema-onafhankelijke
  tint i.p.v. een vast hexgetal. `.nav-item` heeft `!important` op `display`/`padding`/
  `border-radius` omdat de al bestaande `.sidebar a`-regel (element+class-selector) anders qua
  CSS-specificiteit zou winnen van de nieuwere, minder specifieke `.nav-item`-class-regel. Het
  Kanban-kolomkopje krijgt zijn puntkleur via `hsl({{ swimlane.hue }}, ...)` rechtstreeks in de
  template i.p.v. via `swimlane.column_style` (dat laatste geeft een tint+rand-combinatie
  bedoeld voor een hele kolom, niet een los bolletje).
- **Multi-tag filter en geen kleurtint meer op notities**: zelfde aanpak als eerder bij taken
  — `GET /notes?tags=werk&tags=prive` (herhaalde query-param) i.p.v. het vorige losse
  `tag`-param, gefilterd met `Note.tags.any(Tag.name.in_(tags))` (OR-logica). De
  checkbox-lijst toont alleen tags die op een notitie van de gebruiker staan (`Tag` gejoined
  via `Tag.notes`). De checkboxes zelf staan buiten het bulk-acties-`<form>` (dat zou nesten
  betekenen) en zijn met het HTML `form`-attribuut gekoppeld aan een eigen, lege
  `<form id="notes-tag-filter-form">`. `Note.row_tint_style` (de rij-brede kleurtint
  afgeleid van de eerste tag) is verwijderd, net als eerder bij `Task` — de tag-badges zelf
  blijven gekleurd.
- **Achtergrondafbeeldingen**: drie vaste foto's onder `app/static/images/backgrounds/`
  (nature/mountains/space, gedownload van Pexels — vrij te gebruiken, geen attributie
  vereist), bewust self-hosted i.p.v. een live externe API zoals Unsplash/Pexels: geen
  netwerkafhankelijkheid bij het laden van de app, in lijn met de rest van de app die verder
  alleen webfonts extern ophaalt. `user.background`/`user.background_opacity` sturen een
  `data-background`-attribuut en een `--background-opacity`-CSS-variabele op `<html>` (zelfde
  patroon als thema/lettertype/dichtheid). De foto zelf zit in een `position: fixed`-laag
  achter de hele app (`z-index: -2`, met `.layout` expliciet op `z-index: 1` om verrassingen
  met stacking contexts te voorkomen); zichtbaar gemaakt door `.sidebar` en `.main`
  semi-transparant/getint te maken zodat de foto erdoorheen schijnt, terwijl kaarten en
  tabellen daarbovenop hun eigen ondoorzichtige achtergrond houden en dus leesbaar blijven.
- **Mindmap**: `MindmapNode` (tekst, kleur, x/y in pixels) en `MindmapEdge` (koppeling tussen
  twee nodes, richting is puur boekhouding — geen betekenisverschil tussen "van" en "naar").
  Geen library: het canvas is een gewone `position: relative`-container met vrij
  gepositioneerde `.mindmap-node`-`<div>`'s (`position: absolute; left/top`) en een
  overlappende `<svg>`-laag voor de verbindingslijnen, geüpdatet in JS bij het slepen.
  Verbindingslijnen krijgen twee `<line>`-elementen: een dunne zichtbare en een onzichtbare
  bredere eronder (`stroke-width: 12`, transparant) puur om ze makkelijker aanklikbaar te
  maken om te verwijderen — een lijn van 2px raken is anders vrijwel onmogelijk. Bij het
  verwijderen van een node worden diens edges eerst expliciet weggegooid in de route (geen
  ORM-cascade tussen Node en Edge, en SQLite handhaaft de `ON DELETE CASCADE` van de
  foreign keys niet zonder `PRAGMA foreign_keys=ON`, wat deze app niet zet). Posities worden
  pas na het loslaten opgeslagen (niet per pixel tijdens het slepen) om het aantal
  AJAX-verzoeken te beperken.
- **Meerdere mindmaps**: `MindmapBoard` was al een gewoon, niet-uniek-per-gebruiker model
  (net als `Task`/`Note`) — de eerdere "één mindmap per gebruiker"-beperking zat puur in de
  route (`_get_or_create_board` pakte altijd de eerste), niet in het datamodel. Overstappen
  naar meerdere mindmaps was dus een routewijziging, geen migratie: `GET /mindmap` toont nu
  een lijst, `POST /mindmap` maakt een nieuw bord, en de node-/edge-routes checken
  eigenaarschap via een join naar `MindmapBoard.user_id` in plaats van een vast board-id, dus
  ze werken ongeacht in welke van je mindmaps een component zit.
- **Mindmap-tags en -beschrijving**: `MindmapBoard.description` (`Text`) en een nieuwe
  `mindmap_tags`-associatietabel (dezelfde `Tag`, hergebruikt van taken/kanban/notities/
  snippets/kalender) — een compleet nieuwe tabel heeft geen entry in `_COLUMNS_TO_ENSURE`
  nodig, want `Base.metadata.create_all()` maakt ontbrekende tabellen bij het opstarten toch
  al aan; alleen de nieuwe kolom op een bestaande tabel (`description`) moest via een
  lichtgewicht migratie. De lijstpagina hergebruikt de `.note-card`/`.notes-grid`-CSS (zelfde
  kaartvormgeving als notities) i.p.v. iets eigens te bouwen. Bewerken van naam/beschrijving/
  tags gebeurt inline via een `<details>` per kaart i.p.v. een aparte pagina — met een eigen,
  kleine `mindmap-list.js` (i.p.v. `notes-list.js` hergebruiken), want die laatste navigeert
  bij elke klik op de kaart weg tenzij het doelwit expliciet is uitgesloten, en een klik op
  "Bewerken" (`<summary>`) stond daar niet tussen.
- **Mindmap-editor als "fullscreen"**: geen JavaScript Fullscreen API (die heeft een
  gebruikersgebaar nodig en gedraagt zich onvoorspelbaar in een preview/iframe) — gewoon een
  Jinja-`{% block body_class %}` in `base.html` waarmee `mindmap/board.html` een
  `mindmap-editor`-klasse op `<body>` zet. CSS verbergt dan `.sidebar` en geeft `.main` een
  eigen kolom-layout met een smalle bovenbalk (`.mindmap-topbar`) i.p.v. de normale
  pagina-padding. Terugnavigeren naar `/mindmap` (de lijst) herstelt de normale layout
  vanzelf, omdat die pagina de `body_class`-block niet invult.
- **Componenten pas uitklappen bij dubbelklik**: `.mindmap-node-header` (kleur/+/koppel/
  verwijder-knoppen) staat standaard op `display: none` en wordt getoond via de
  `.mindmap-node-expanded`-klasse, die `mindmap.js` toggelt op dubbelklik (met een check dat
  een dubbelklik ín de tekst zelf — om een woord te selecteren — de werkbalk niet opent) en
  weer verwijdert bij een klik buiten het component.
- **API-authenticatie**: een los, willekeurig token (`secrets.token_urlsafe(32)`), waarvan
  alleen de SHA-256-hash in `User.api_token_hash` staat — zelfde patroon als
  `password_hash`. De nieuwe dependency `require_api_user` (naast het bestaande
  `require_user` voor de sessie-cookie) leest de `Authorization: Bearer <token>`-header,
  hasht 'm en zoekt de gebruiker erbij op; geen match of ontbrekende header geeft direct 401.
  De `/api/v1/...`-routes zijn een aparte, JSON-in/JSON-uit-laag naast de bestaande
  form-based/HTML-routes en hergebruiken dezelfde services (`resolve_tags`,
  `sanitize_note_html`) zodat een via de API aangemaakte taak/notitie/kaart/snippet zich
  identiek gedraagt aan eentje via de webinterface. Voor kanban-kaarten zonder opgegeven
  swimlane/kolom wordt de eerste swimlane + eerste kolom van het bord gebruikt (en zo nodig
  aangemaakt), zodat een agent niet eerst de bordstructuur hoeft op te vragen.
- **Backup via `VACUUM INTO`**: export leest niet zomaar het live `.db`-bestand, maar laat
  SQLite zelf (`VACUUM INTO`) een consistente, gecomprimeerde kopie wegschrijven naar een
  tijdelijk bestand — dat kan veilig naast een lopende app, in tegenstelling tot een
  bestandskopie tijdens een schrijfactie. Het databasepad wordt afgeleid uit
  `settings.database_url` (niet hardcoded `app.db`), zodat het ook in tests met een eigen
  `DATABASE_URL` werkt. Bij importeren wordt eerst gevalideerd dat het bestand een
  SQLite-header heeft én de kerntabellen bevat (`users`, `tasks`, `tags`) voordat er iets
  overschreven wordt; de huidige database wordt eerst gekopieerd naar
  `app.db.before-import-<tijdstip>` als veiligheidsnet. Na het vervangen van het bestand
  draaien `Base.metadata.create_all` en de lichte migraties opnieuw, zodat een back-up van
  een oudere appversie (bv. van vóór de mindmap- of achtergrond-kolommen) automatisch
  bijgewerkt wordt naar het huidige schema. De sessie van de gebruiker wijst na een import
  niet meer zeker naar een geldige rij, dus wordt er teruggestuurd naar `/login`.
- **Voice-notitie als losse container, niet ingebakken**: Whisper-modellen zijn zwaar
  (CPU/RAM, extra Python-dependencies) en horen niet thuis in de lichte hoofd-image die het
  hele "single-container Docker"-uitgangspunt van deze app draagt. In plaats daarvan praat
  `app/routers/voice.py` via `httpx` met een losse, zelf-gehoste Whisper-webservice
  (`WHISPER_SERVICE_URL`, zie Configuratie) — dezelfde reden waarom er geen lokaal LLM
  ingebakken zit voor de latere commando-interpretatie. Is die container niet bereikbaar,
  dan geeft de route een duidelijke 503 met uitleg i.p.v. een generieke serverfout.
- **Fase 1 bewust beperkt tot "altijd een notitie"**: spraak wordt nu altijd een gewone
  notitie (hergebruikt de bestaande `/notes`-route en `sanitize_note_html`), zonder
  automatische keuze tussen taak/kanban-kaart/snippet en zonder matching op bestaande
  items — dat is de geplande fase 2 (ChatGPT-interpretatie + eigen bevestigingsscherm, zie
  BACKLOG.md). Het bewerkbare transcript-tekstvak vóór opslaan is de bevestigingsstap van
  fase 1: spraakherkenning gaat af en toe mis, en dit voorkomt dat een verkeerd verstane
  zin direct als notitie wordt opgeslagen.
- **`openai_api_key` bewust leesbaar opgeslagen, niet gehasht**: in tegenstelling tot
  `api_token_hash` (die de app alleen hoeft te *vergelijken*) moet de OpenAI-sleutel straks
  weer teruggelezen kunnen worden om 'm mee te sturen bij calls naar de OpenAI API — een
  hash is daarvoor onbruikbaar. Blijft binnen de eigen SQLite-database en wordt nooit naar
  de browser teruggestuurd (alleen de laatste 4 tekens, ter herkenning welke sleutel actief
  is).
