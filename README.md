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
  een klikbare markdown-link van maakt). **Tags staan niet op de kaart zelf op het bord** —
  ruimtebesparing op een bord met veel kaarten — maar wél in het tags-veld van deze
  bewerk-modal
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
  een **"dagtaak"-vinkje** (☀) is een tweede, onafhankelijk vinkje naast prioriteit — zo'n
  taak krijgt een zonnetje voor de titel én de hele kaart een oranje linkerrand + subtiele
  oranje tint, zodat dagelijkse taken in één oogopslag opvallen tussen de rest;
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
- **Favicon**: het browsertabblad-icoon is nu een oranje "P" op antraciet
  (`app/static/images/favicon.svg`) — dezelfde kleuren (`#ef8354` op `#262a36`) als het
  "Productivity Suite"-merklabel bovenaan de sidebar. Er bestond nog geen apart logo-bestand
  (het merklabel was tot nu toe alleen gestylede tekst), dus is dit het eerste echte
  grafische "logo" van de app, gebruikt op precies twee plekken: de favicon en (indirect,
  qua kleurkeuze) het merklabel
- **Kanban-kaarttitels in het merk-oranje**: dezelfde vaste `#ef8354` als het
  "Productivity Suite"-merklabel en de favicon, i.p.v. de gewone tekstkleur — een derde
  plek die nu dat merk-oranje gebruikt. Bewust hardgecodeerd i.p.v. `var(--accent)`, dat per
  thema verschilt, want dit specifieke oranje moet er in élk thema hetzelfde uitzien
- **Nieuw thema "Bubbles"**: een 10e thema (naast dracula/one-dark-pro/nord/light/nexmail/
  macos-light/anchor/anchor-solid/white) waarin taak-, notitie- en snippet-kaarten met een
  tag een **volle, solide achtergrondkleur** krijgen (van de eerste tag, net als de
  tag-bubbels zelf) met een **zachte schaduw i.p.v. een rand** — kaarten zonder tag blijven
  een gewone, neutrale kaart. Kiesbaar via dezelfde thema-zwaaitjes in de sidebar als de
  andere thema's (laatste, regenboogkleurige swatch)
- **Weergave-instellingen** (Account → Weergave): los van het thema kiesbaar **lettertype**
  (16 opties — systeemstandaard, de leesletters Inter/Roboto/Open Sans/Lato/Poppins/Nunito/
  Source Sans 3/Merriweather/Fira Sans/DM Sans, het sierlijke schreefletter Playfair Display,
  en de monospace/code-letters Hack/JetBrains Mono/Fira Code/Consolas), **lettergrootte**
  (11–18px) en **compactheid** (comfortabel/compact,
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
  lijst om op meerdere tags tegelijk te filteren (OR-logica). **Tags staan niet meer op de
  notitiekaart zelf** in het overzicht (raster/lijst) — dat bespaart ruimte bij veel notities
  — maar wél zichtbaar en aanpasbaar in het "Tags"-veld van het edit-formulier. De hele kaart in de
  lijstweergave is klikbaar om te bewerken, en een **selectievak per notitie** maakt
  bulk-acties mogelijk: meerdere notities in één keer verwijderen of er samen een tag aan
  toevoegen. Een **"Tijdelijke notitie"-vinkje** markeert een notitie als **temp** (zichtbaar
  als badge in de lijst) — zo'n notitie wordt automatisch verwijderd zodra ze een week oud is.
  Een **afbeelding plakken** (bv. met cmd/ctrl+V vanaf een screenshot) voegt hem direct in op de
  cursorpositie, met afgeronde hoeken, en blijft behouden na opslaan.
- **Stickies (plakbriefjes)**: eigen pagina `/stickies` (sidebar → Stickies) met gekleurde
  briefjes in een raster. Per sticky: platte tekst, **kleur** (geel/roze/blauw/groen/oranje/
  paars, vaste pastelkleuren onafhankelijk van het thema), **tags** (zelfde gedeelde tag-systeem,
  klikbaar om te filteren) en een **Temp**-vinkje — een temp-sticky wordt na een week
  automatisch verwijderd (zelfde opportunistische opruiming bij elk bezoek als tijdelijke
  notities). Wijzigingen worden direct via `fetch` automatisch opgeslagen (`stickies.js`,
  server antwoordt 204 op het `X-Requested-With: fetch`-verzoek), zonder opslaan-knop of
  paginaherlaad; nieuw toevoegen via het briefje bovenaan.
  In het overzicht zie je alleen de klassieke briefjes (licht gedraaid, handschriftlettertype,
  alleen tekst); kleur, tags en temp zitten achter het ⚙-knopje op elk briefje.
- **Kanban: lanes standaard ingeklapt**: een vinkje "Lanes standaard ingeklapt" naast de
  bordtitel laat bij elke paginalading alle swimlanes dicht starten (alleen de lane-namen
  zichtbaar). Individueel openklappen kan, maar wordt dan niet onthouden. Voorkeur staat in
  `localStorage` (client-side, geen serverstate).
- **Herhalende afspraken**: een kalenderafspraak kan **elke week** of **elke maand** herhalen
  (optioneel "Herhalen tot"-datum). Eén rij in de database; de voorkomens worden per
  weergegeven bereik uitgerekend (`app/services/recurrence.py`), dus ze verschijnen in maand-,
  week- en mini-kalender met een ↻ ervoor. Maandelijks op de 31e valt in kortere maanden op de
  laatste dag. "**Herhaling stoppen**" in het bewerkformulier laat voorkomens t/m vandaag staan
  en laat de rest verdwijnen; verwijderen haalt de hele reeks weg. Onder de kalender staat een
  nieuw blok **Herhalende afspraken** met per reeks frequentie, volgende datum en einddatum.
- **Dagtaken vallen op**: een taak met "Dagtaak" aangevinkt heeft een magenta titel, een
  gradient van zwart (links) naar oranje (rechts) en een rustig knipperende oranje rand (uit
  bij `prefers-reduced-motion`); geldt in elk thema.
- **Taakkleur via tags**: een taak met een tag krijgt een zachte gradient van de (gedempte)
  tagkleur links naar de kaartkleur van het actieve thema rechts (`color-mix` met
  `--bg-elevated`, dus ook leesbaar in lichte thema's); "Bubbles" gebruikt dezelfde gradient
  maar met een sterkere tagkleur (`--task-tag-strength`).
- **Taken-archief**: een afgeronde taak verdwijnt 24 uur na afvinken uit de takenlijst (en
  kalender/zoeken/graph) en komt in het **Archief** (knop "Archief" op de takenpagina,
  `/tasks/archive`). Daar kun je 'm **herstellen** (terug naar "todo") of definitief
  verwijderen; na 30 dagen in het archief wordt hij automatisch verwijderd. Opportunistisch
  bij elk bezoek, geen scheduler (kolom `tasks.archived_at`).
- **Automatische back-ups**: een achtergrond-thread (`app/services/backup.py`) maakt bij het
  starten en daarna elk uur een check: max. één database-backup per dag
  (`data/backups/app-YYYYMMDD.db`, via `VACUUM INTO`, de laatste 14 blijven bewaard) en elke
  snippet die nog niet (of gewijzigd) in de backup staat wordt als `data/backups/snippets/<id>.json`
  weggeschreven. Er wordt nooit iets uit de snippet-backup verwijderd, dus ook een in de app
  verwijderde snippet blijft terug te vinden. Uitzetten kan met `BACKUP_ENABLED=false`.
- **Notities sorteren + raster-/lijstweergave**: een "Sorteren op"-keuzelijst (laatst
  gewijzigd / titel / aangemaakt, server-side, blijft staan bij tag-filteren en bulk-acties)
  en een **▦ Raster / ☰ Lijst-schakelaar** ernaast. Lijstweergave toont elke notitie als
  compacte rij (titel, tags, datum) i.p.v. een kaart — puur client-side CSS/JS (geen extra
  server-call), gekozen weergave onthouden in `localStorage` zodat ze blijft staan bij een
  volgend bezoek
  De notitiekaarten zelf zijn herontworpen naar de vormgeving van
  [zhfahim/anchor](https://github.com/zhfahim/anchor): sterk afgeronde hoeken, volledig
  ronde tag-pills met een "#"-prefix, en de datum onderaan de kaart
- **Code snippets** (ByteStash-stijl, zie [github.com/jordan-dalby/ByteStash](https://github.com/jordan-dalby/ByteStash)):
  een snippet kan **meerdere bestanden** bevatten (bv. `main.py` + `requirements.txt` bij
  elkaar), elk met een eigen taal voor **syntax highlighting** (highlight.js) — de taal
  wordt **automatisch afgeleid uit de bestandsextensie** zodra je een bestandsnaam typt
  (bv. `config.json` → json, `app.py` → python), en blijft daarna gewoon handmatig aan te
  passen via de select. Kaarten staan **in een raster** (net als notities), qua opbouw
  gemodelleerd naar ByteStash: **titel + relatieve tijd** ("3 dagen geleden") bovenaan,
  een optionele **beschrijving** (2 regels, "Geen beschrijving beschikbaar" als er geen
  is), **tags als pillen** ("Geen tags" als placeholder), en direct een **live preview van
  het eerste bestand** — een bestandsnaam-balkje met **kopieer-** en **uitklap-iconen**,
  daaronder de gesyntax-highlighte code (bij meerdere bestanden: "+ N meer bestanden"
  eronder). Klik op de titel, het uitklap-icoon, of "+ N meer bestanden" om alles te
  bekijken in een **bijna-volledig-scherm paneel**, met **regelnummers**
  (highlightjs-line-numbers.js) naast de syntax highlighting, voor een stuk betere
  leesbaarheid bij langere snippets. In dat paneel kun je de code ook direct **bewerken**
  ("Bewerken" → tekstvak(-ken) per bestand → "Opslaan" of "Annuleren") zonder naar het
  volledige bewerkformulier te hoeven — handig voor een snelle correctie, terwijl
  titel/beschrijving/tags/bestand-toevoegen nog steeds via "Bewerken" op de kaart zelf gaat.
  Eén zoekveld doorzoekt titel, tag én code-inhoud tegelijk, taggable met hetzelfde gedeelde
  tag-systeem. De "Bewerken"/"Verwijder"-knoppen op de kaart zijn **kleiner** (`.btn-sm`)
  zodat ze minder aandacht opeisen dan de titel, en een **selectievak per snippet** maakt
  (net als bij notities) **bulk-verwijderen** van meerdere snippets in één keer mogelijk —
  de hele lijst staat in één formulier, met een selectiebalk die verschijnt zodra je iets
  aanvinkt. De **scrollbar in de code-preview is een vaste, donkere kleur** i.p.v. de
  systeemstandaard (vaak wit) — de code-achtergrond komt van highlight.js'
  atom-one-dark-stylesheet, die altijd donker is ongeacht het actieve app-thema, dus een
  scrollbar in de thema-kleur (wit bij bv. het "white"-thema) zou er juist tussenuit
  springen i.p.v. erbij horen
- **Snippets exporteren/importeren**: een **"⇅ Export / Import"-paneel** boven de
  snippetlijst laat je al je snippets **exporteren als JSON** (herimporteerbaar, geen
  database-id's, dus ook bruikbaar om over te zetten naar een andere installatie) of als
  **Markdown** (leesbaar/deelbaar document, niet bedoeld om terug te importeren). JSON
  **importeren** voegt de snippets uit het bestand toe aan je bestaande snippets (overschrijft
  niks) — bij een ongeldig/beschadigd bestand krijg je een duidelijke foutmelding i.p.v. een
  kale foutpagina. Bewust een lichtgewicht, snippet-only export/import, los van de
  hele-database-backup onder Account → Backup
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
  kanban-kaarten/-swimlanes, notities en code-snippets kan aanmaken via `/api/v1/tasks`,
  `/api/v1/kanban/swimlanes`, `/api/v1/kanban/cards`, `/api/v1/notes` en `/api/v1/snippets`
  (JSON in, JSON uit). Een kanban-kaart aanmaken zonder swimlane/kolom op te geven belandt
  automatisch in de eerste kolom van de eerste swimlane; een nieuwe swimlane krijgt meteen
  de standaardkolommen (Backlog/Todo/In Progress/Done), net als via de browser-UI. Het token
  wordt maar één keer getoond (alleen de hash wordt bewaard) en is op elk moment in te
  trekken
- **Backup** (Account → Backup): de hele database (taken, kanban, notities, snippets,
  kalender, mindmap, instellingen) in één keer **exporteren** als downloadbaar `.db`-bestand,
  en later weer **importeren** om alles terug te zetten — er wordt automatisch eerst een
  veiligheidskopie van de huidige database gemaakt voordat 'm vervangen wordt
- **Quick-add-wiel**: een ronde hub-knop rechtsonder (op elke pagina, met een 4-stippen-icoon)
  die bij een klik openklapt naar een **semi-transparant rond menu** met 5 taartpunten —
  **Notities**, **Kanban**, **Snippets**, **Taken** en **Mindmap** — elk met een eigen icoon en
  label, die direct doorlinken naar de bijbehorende aanmaakpagina (`/notes/new`, `/kanban`,
  `/snippets/new`, `/tasks/new`, `/mindmap`). Klik ergens buiten het wiel of druk op Escape om
  het weer te sluiten. **30% kleiner en zelfde donkere-glas-look als de Pomodoro-widget**:
  geen felgekleurde taartpunten meer (was een conic-gradient met 6 losse kleuren), nu een
  egale donkere achtergrond (`rgba(20, 20, 25, 0.55)`, `backdrop-filter: blur`) met
  dezelfde oranje gloed-rand — dezelfde stijl-taal als de Pomodoro-cirkel
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
  doorstuurt naar een **losse, zelf-gehoste Speaches-container** (voorheen
  faster-whisper-server, zie Configuratie hieronder) voor de transcriptie. Een
  **taal-keuzelijst** (Automatisch detecteren / Nederlands / English, onthouden in
  `localStorage`) laat je de taal expliciet meegeven — vooral bij kleinere Whisper-modellen
  ("tiny") is dat een stuk betrouwbaarder dan automatische taaldetectie, die bij korte
  fragmenten weleens de verkeerde taal raadt of talen door elkaar mixt. Je ziet en
  corrigeert het transcript zelf vóórdat je opslaat — dat is bewust de bevestigingsstap,
  want spraakherkenning gaat af en toe mis. Een **"Opslaan als"-keuzelijst** (Notitie / Taak
  / Kanban-kaart / Snippet, onthouden in `localStorage`) plus een eigen **tags-veld**
  bepalen naar welke bestaande create-route het transcript gaat (`/notes`, `/tasks`,
  `/kanban/cards` of `/snippets`) — bij een taak/kanban-kaart wordt de rauwe
  transcript-tekst de beschrijving (die tonen platte/markdown-tekst, geen HTML-editor zoals
  notities), bij een snippet wordt het één bestand (`notitie.txt`, plaintext). Een
  kanban-kaart komt in de eerste cel van je bord terecht (`GET /kanban/default-cell`,
  hergebruikt door fase 2 hieronder) — er is vanuit voice geen UI om zelf een cel te kiezen,
  maar de kaart is daarna gewoon te verslepen. De knoptekst ("Opslaan als ...") past zich
  live aan je keuze aan.
- **Voice-notitie fase 2: AI bepaalt het type**: een **"✨ Laat AI het type
  bepalen"-knop** in hetzelfde opnamepaneel stuurt het (al gecontroleerde) transcript naar
  `POST /voice/classify` (`app/routers/voice.py`), die ChatGPT (`gpt-4o-mini`, JSON-output)
  laat bepalen of het een taak/notitie/kanban-kaart/snippet moet worden, plus een titel en
  tags voorstelt. Bewust **alleen** type/titel/tags — de inhoud blijft het transcript dat je
  net zelf gecontroleerd hebt (fase 1's bevestigingsstap), zodat er geen tweede laag
  AI-herschrijving boven op de spraakherkenning komt. Het resultaat vult de
  "Opslaan als"-keuzelijst, het titelveld en het tags-veld alvast in, met een tekstregel
  ("AI denkt: taak 'Boodschappen doen' — controleer de velden en klik op ...") — je klikt
  daarna nog steeds zelf op de "Opslaan als ..."-knop, dát is de eigenlijke
  bevestigingsstap (in plaats van een apart bevestigingsscherm: de velden staan al
  zichtbaar/bewerkbaar in hetzelfde paneel). Vereist een ingestelde OpenAI-sleutel (zie
  hieronder) — zonder sleutel geeft de knop een duidelijke foutmelding i.p.v. een vage 500.
  De **OpenAI-sleutel** stel je in via Account → OpenAI API-sleutel, met een
  **"Sleutel testen"-knop** die de zojuist ingevulde (nog niet per se opgeslagen)
  sleutel direct tegen `GET https://api.openai.com/v1/models` test en meldt of 'm werkt —
  zonder dat je eerst hoeft op te slaan of ergens anders hoeft te controleren. De
  Speaches-**service-URL en modelnaam zijn nu ook via Account → Whisper / Speaches
  in te stellen** (i.p.v. alleen via de WHISPER_SERVICE_URL/WHISPER_MODEL-omgevingsvariabelen
  van de container — die blijven werken als fallback zolang het veld leeg is), met een
  eigen **"Verbinding testen"-knop** die `GET {url}/v1/models` opvraagt en controleert of
  het ingestelde model daar ook echt bij staat (i.p.v. alleen "is de service bereikbaar")
- **Voice: bestaand audiobestand uploaden + samenvatten met AI**: naast live opnemen kun je
  in hetzelfde paneel ook een **bestaand audiobestand uploaden** (mp3/wav/m4a/...) — gaat
  door dezelfde `POST /voice/transcribe`-route als een eigen opname (Speaches maakt geen
  onderscheid tussen audio van de microfoon of van schijf). Handig voor bv. een opname die
  je met een andere app hebt gemaakt (voice-memo op je telefoon, een vergaderopname). Een
  nieuwe **"📝 Samenvatten met AI"-knop** (naast "✨ Laat AI het type bepalen") stuurt het
  transcript naar `POST /voice/summarize`, dat ChatGPT een beknopte samenvatting laat maken
  en die in het transcript-tekstvak zet — handig bij een langere opname (bv. een
  vergadering) waar je liever de kern opslaat dan de volledige letterlijke tekst. Net als
  bij classificeren blijft dit bewerkbaar vóór opslaan, en vereist het dezelfde
  OpenAI-sleutel. Mindmap-generatie uit een transcript staat nog niet op de planning (zie
  BACKLOG.md) — dat vraagt om ChatGPT die zelf knopen/verbindingen bedenkt i.p.v. platte
  tekst, een stuk complexer dan transcript/samenvatting.
- **Zoeken** (nieuw menu-item "Zoeken", `/search`): één zoekscherm over **alle** taggable
  soorten items heen (taken, notities, kanban-kaarten, snippets, mindmaps,
  kalenderafspraken) — op los woord (titel/inhoud, `ILIKE`) en/of op een specifieke tag,
  allebei tegelijk mag ook (dan moet een item aan beide voldoen). Resultaten worden per
  soort gegroepeerd getoond, met een link naar de bewerkpagina (kanban-kaarten linken naar
  het hele bord, want die hebben geen eigen pagina — ze worden inline op het bord bewerkt).
  De tag-keuzelijst toont alle tags in het systeem (`Tag` heeft bewust geen `user_id`, zie
  Architectuur), niet per-gebruiker gefilterd — voor een single-user-per-deployment app
  maakt dat niets uit.
- **Kanban: taak toevoegen, swimlane hernoemen/verwijderen**: elke kolomcel heeft nu ook een
  **"+ Taak toevoegen"**-keuzelijst (naast "+ Kaart toevoegen") met je nog-niet-afgeronde
  taken die nog niet als kaart op het bord staan — kiezen kopieert titel/beschrijving/tags
  eenmalig naar een nieuwe kaart en onthoudt de koppeling (✓-icoontje op de kaart, linkt naar
  de taak). Elke swimlane-kop heeft nu een **✎ Naam wijzigen**-knop (klein inline
  formuliertje) en, zodra er meer dan één swimlane is, een **🗑 Swimlane verwijderen**-knop
  (met bevestiging — verwijdert ook alle kolommen/kaarten erin). De allerlaatste swimlane
  van een bord kun je niet verwijderen, anders zou je geen "+ Kaart toevoegen"-plek meer
  overhouden zonder eerst zelf een nieuwe swimlane aan te maken.
- **Taken: automatisch opruimen + "lang niet aangeraakt"-markering**: een afgeronde taak
  ruimt zichzelf automatisch op **4 dagen** nadat 'm op "klaar" gezet is (opportunistisch bij
  elk bezoek aan de takenlijst, geen aparte scheduler — zelfde patroon als tijdelijke
  notities). Een taak die meer dan **7 dagen niet bewerkt** is (ongeacht status) krijgt een
  witte linkerrand + lichte tint op de kaart, zodat je in één oogopslag ziet wat is blijven
  liggen.
- **Filter & sorteren achter één knop** (Taken, Notities): de sorteer-keuzelijst en alle
  tags-als-checkboxes stonden eerst permanent open in de toolbar — nu zitten ze achter een
  **"⚙ Filter & sorteren"-knop** die standaard dichtklapt, met een badge die het aantal
  actieve tag-filters toont zolang het paneel dicht is. Rustiger standaardscherm zonder dat
  je de filter/sorteer-opties kwijtraakt.
- **Swimlane hernoemen — pop-up bleef eerst buiten beeld (BUGFIX)**: het ✎-formuliertje
  opende naar rechts vanaf een icoon dat al helemaal rechts in de (mogelijk brede,
  horizontaal scrollbare) swimlane-kop stond, waardoor het tekstveld goeddeels onzichtbaar
  was. Het pop-up opent nu naar links i.p.v. naar rechts, met een vaste breedte voor het
  tekstveld.
- **Nieuws-ticker onderin**: een dunne balk onderaan elke pagina laat je nog niet
  afgeronde **prioriteit-taken** (alleen die met "Prioriteit" aangevinkt — anders zou de
  band bij veel taken al snel te druk/lang worden) langzaam van rechts naar links voorbij
  glijden (net als een nieuwsband onder een tv-uitzending), elk herkenbaar aan een ★ en
  klikbaar naar de bewerkpagina. Met een sluitknopje te verbergen (onthouden in
  `localStorage`); de quick-add-wheel en Pomodoro-widget schuiven automatisch een stukje
  omhoog zolang de ticker zichtbaar is, en weer terug zodra 'm verborgen is.
- **Kanban: 5 standaardkolommen + gekleurde stippenlijn-dividers**: nieuwe swimlanes (en het
  bord van een gloednieuwe installatie) krijgen nu **Backlog / To Do / In Progress / Review /
  Done** i.p.v. de eerdere 4 (Backlog/Todo/In Progress/Done) — bestaande swimlanes op een
  al langer lopende installatie veranderen niet met terugwerkende kracht, dit geldt alleen
  voor nieuw aangemaakte. Tussen de kolommen staat nu een **gekleurde stippenlijn** die per
  kolomgrens van kleur wisselt (roze → oranje → blauw → groen, dan weer opnieuw), met een
  korte gradient die vanaf de lijn vervaagt naar transparant.

Nog niet gebouwd: CI/CD, voice-commando's matchen op een al bestaand item i.p.v. altijd een
nieuw item aanmaken (bv. "voeg dit toe aan mijn boodschappenlijst-notitie" i.p.v. een nieuwe
notitie — de classificatie zelf, welk type item het moet worden, werkt al via ChatGPT, zie
hierboven), verdere LLM-koppeling (er is nu wel een API voor scripts/agents, zie hieronder).

## Configuratie

Geen `.env`-bestand of omgevingsvariabelen nodig. Bij de eerste start:
- wordt een sessie-secret-key automatisch gegenereerd en opgeslagen in `data/.secret_key`
  (blijft geldig na herstarts/updates, zolang het data-volume bewaard blijft);
- wordt een seed-account aangemaakt: gebruikersnaam `admin`, wachtwoord `admin`.

Voor voice-notities heb je een **losse Speaches-container** nodig (voorheen
faster-whisper-server — draait niet mee in de hoofd-image, zie architectuur hieronder).
Speaches praat de OpenAI Audio API na (`POST /v1/audio/transcriptions`), dus als je 'm al
op Unraid draait (bv. via de Community Applications-app "faster-whisper" / "Speaches")
hoef je alleen twee dingen door te geven:
- de **URL** van je Speaches-container (bv. `http://<unraid-ip>:8000` als je 'm niet in
  hetzelfde Docker-netwerk draait)
- de exacte **modelnaam** die Speaches geladen heeft (kijk in de Speaches-logs of -UI welk
  model actief is) — komt dit niet overeen, dan geeft `/voice/transcribe` een duidelijke
  502-foutmelding met de modelnaam die niet klopte

**Makkelijkste manier**: Account → Whisper / Speaches → vul de service-URL en modelnaam in,
klik "Verbinding testen" om te checken of het klopt (nog vóór opslaan), en klik "Opslaan".
Dit is een **per-gebruiker instelling in de database** (`User.whisper_service_url`/
`whisper_model`), geen omgevingsvariabele — dus geen container-herstart nodig en direct
aan te passen vanuit de app zelf.

**Alternatief**: de env vars `WHISPER_SERVICE_URL`/`WHISPER_MODEL` op de container zelf
zetten (bv. handig als vaste fallback/default voor alle gebruikers, of als je liever bij
infra-as-config blijft). De instelling via de Settings-pagina wint als beide gezet zijn;
laat je het Settings-veld leeg, dan val je terug op de env var. **Waar zet je die env vars
precies neer?** Hangt af van hoe je de container beheert:
- **Via `scripts/install-unraid.sh`** (aanbevolen als je dat script gebruikt): vul
  `WHISPER_SERVICE_URL`/`WHISPER_MODEL` in bij het configuratieblok bovenaan het script,
  of zet ze als shell-omgevingsvariabele vóór het draaien:
  ```bash
  WHISPER_SERVICE_URL=http://192.168.1.50:8000 \
  WHISPER_MODEL=Systran/faster-whisper-base \
  bash install-unraid.sh
  ```
  Het script geeft ze door aan de container en meldt aan het einde of voice-notities
  geconfigureerd zijn.
- **Via de Unraid Docker-GUI** (als je de container los beheert, niet via het script):
  ga naar **Docker** → klik op de "productivity-suite"-container → **Edit** → onderaan
  **"Add another Path, Port, Variable, Label or Device"** → kies **Variable**, vul als
  **Key** `WHISPER_SERVICE_URL` in en als **Value** de URL, herhaal voor `WHISPER_MODEL` →
  **Apply** (herstart de container automatisch).
- **Lokaal met `docker compose up`**: zet ze onder `environment:` in `docker-compose.yml`.

Draai je Speaches nog niet: zoek in Unraid Community Applications naar "faster-whisper" of
"Speaches" en installeer die met een CPU- of GPU-image naar keuze (afhankelijk van je
hardware) — de exacte poort en modelnaam die je daarbij instelt, gebruik je hierboven voor
`WHISPER_SERVICE_URL`/`WHISPER_MODEL`.

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
    een draaiende Speaches-container (of met een verkeerde `WHISPER_SERVICE_URL`): druk op
    opnemen, spreek iets in, druk nogmaals om te stoppen → na even wachten verschijnt een
    duidelijke foutmelding ("Kan de Whisper-service niet bereiken..."). Zet
    `WHISPER_SERVICE_URL` goed maar `WHISPER_MODEL` fout → een andere foutmelding met het
    HTTP-statuscode en de responstekst van Speaches erin (bv. "model not found"), zodat je
    kunt zien welk modelnaam wél geladen is. Zet ook `WHISPER_MODEL` goed en herhaal de
    opname → het transcript verschijnt in een bewerkbaar tekstvak met een voorgestelde
    titel. Pas het eventueel aan en klik "Opslaan als notitie" → je komt op de
    notities-pagina en de nieuwe notitie staat er met het (aangepaste) transcript in.
28. Ga naar Account → OpenAI API-sleutel. Klik "Sleutel testen" zonder iets in te vullen →
    "Vul eerst een sleutel in." verschijnt in rood. Typ een willekeurige/onechte sleutel
    (bv. "sk-test") en klik nogmaals → na een korte call naar de echte OpenAI API verschijnt
    "Ongeldige sleutel (401 Unauthorized)." Vul je eigen echte OpenAI-sleutel in en test
    opnieuw → "Sleutel werkt." in groen. Sla de sleutel op en controleer dat "Sleutel
    testen" ook zonder iets in het veld te typen werkt (test dan de al-opgeslagen sleutel).
29. Maak een paar notities aan met duidelijk verschillende titels → ga naar Notities en klik
    "☰ Lijst" → de kaarten worden compacte rijen (titel, datum). Herlaad de pagina →
    de lijstweergave blijft staan (localStorage). Kies bij "Sorteren op" → "Titel" →
    controleer dat de notities alfabetisch gesorteerd staan, ook nog in lijstweergave. Vink
    een tag aan om te filteren → de sortering blijft "Titel". Klik terug naar "▦ Raster" →
    de kaartweergave komt terug.
30. Maak een notitie én een kanban-kaart aan met een paar tags → controleer dat er nergens
    een tag-badge op de notitiekaart (raster én lijst) of op de kanban-kaart op het bord
    verschijnt. Open de notitie om te bewerken → de tags staan gewoon in het "Tags"-veld.
    Klik "Bewerken" op de kanban-kaart → de tags staan in het tags-veld van de modal. Maak
    daarna een notitie aan, bulk-verwijder 'm meteen, en maak direct een nieuwe notitie aan
    met andere tags → controleer dat die nieuwe notitie **niet** de tags van de verwijderde
    notitie heeft overgenomen (regressietest voor de foreign-key-bugfix hieronder).
31. Maak een taak aan en vink "Dagtaak" aan (naast "Prioriteit") → controleer dat de taak in
    de takenlijst een ☀-icoon voor de titel krijgt én dat de hele kaart een oranje
    linkerrand + subtiele oranje tint heeft. Vink ook "Prioriteit" aan op dezelfde taak →
    beide iconen (★ en ☀) staan naast elkaar voor de titel.
32. Maak een snippet aan met een langer codebestand (20+ regels) → ga naar Snippets en klik
    op de titel → een bijna-volledig-scherm paneel opent met de code, **regelnummers** links
    en **syntax highlighting**. Sluit het (kruisje, klik naast het paneel, of Escape) en open
    dezelfde snippet nogmaals → de regelnummers verschijnen nog steeds correct (niet dubbel
    of ontbrekend).
33. Open diezelfde snippet in het fullscreen-paneel en klik "Bewerken" → de code (met
    meerdere regels, inclusief inspringing) verschijnt in een tekstvak. Pas een regel aan
    en klik "Opslaan" → de pagina herlaadt en de aangepaste code staat er (open de snippet
    opnieuw om te controleren dat regeleindes/inspringing intact bleven — dat was een
    bug tijdens het bouwen: regelnummers herstructureren de code in een tabel, waardoor
    `\n`-tekens verloren gaan als je niet oplet). Open nogmaals "Bewerken", wijzig iets,
    maar klik nu "Annuleren" → de oorspronkelijke code (vóór de laatste, wél opgeslagen
    wijziging) verschijnt weer, zonder dat er iets is opgeslagen.
34. Ga naar Account → Whisper / Speaches → vul een willekeurige URL in en klik "Verbinding
    testen" → een rode foutmelding verschijnt (kan geen verbinding maken). Vul de URL van
    je echte Speaches-container in (en eventueel modelnaam) en test opnieuw → "Verbinding
    gelukt" in groen, met een melding of het ingestelde model ook echt geladen is. Klik
    "Opslaan" en herlaad de pagina → de waarden staan er nog. Neem daarna een voice-notitie
    op (zie stap 27) → die gebruikt nu deze per-gebruiker instelling i.p.v. de
    WHISPER_SERVICE_URL/WHISPER_MODEL-omgevingsvariabelen van de container.
35. Maak drie snippets aan → ga naar Snippets en controleer dat "Bewerken"/"Verwijder" op
    elke kaart merkbaar kleiner zijn dan voorheen. Vink het selectievakje van twee snippets
    aan → een selectiebalk verschijnt bovenaan met het aantal geselecteerd en een
    "Verwijderen"-knop. Klik die knop (bevestig de confirm-dialoog) → beide geselecteerde
    snippets verdwijnen, de derde blijft staan.
36. Open het opnamepaneel (🎤 Voice) → een "Taal"-keuzelijst staat boven de opnameknop met
    "Automatisch detecteren"/"Nederlands"/"English". Kies "English", sluit het paneel en
    open het opnieuw → "English" staat nog steeds geselecteerd (localStorage). Neem een
    Engelse zin op → het transcript moet er nu stukken betrouwbaarder uitzien dan met
    automatische detectie, vooral bij een klein Whisper-model.
37. Zet in het opnamepaneel "Opslaan als" op "Taak" → de knop onderaan heet nu "Opslaan als
    taak". Neem iets op en sla op → je komt op de takenlijst en de nieuwe taak staat er met
    het transcript als beschrijving. Open het paneel opnieuw → "Taak" staat nog steeds
    geselecteerd. Zet "Opslaan als" terug op "Notitie", neem nogmaals iets op en sla op → je
    komt nu op de notitielijst met een gewone notitie.
38. Ga naar "Zoeken" in de sidebar → zonder iets in te vullen zie je een uitleg-tekst, geen
    resultaten. Maak een taak en een notitie aan met hetzelfde woord in de titel (bv.
    "Feestplanning") en dezelfde tag → zoek op dat woord: beide staan gegroepeerd onder
    "Taken"/"Notities" met een klikbare titel. Zoek in plaats daarvan op de tag via de
    keuzelijst → dezelfde twee resultaten komen terug. Vul zowel een woord als een tag in
    die niet allebei bij hetzelfde item horen → 0 resultaten.
39. Log uit en ga naar `/` (of log opnieuw in) → je komt automatisch op de Kalender terecht
    (dat was al zo, geen losse instelling nodig).
40. Open het opnamepaneel (🎤 Voice) → naast "Opslaan als" staat nu ook een Tags-veld. Zet
    "Opslaan als" op "Kanban-kaart", neem iets op en sla op → je komt op het kanbanbord en de
    kaart staat in de eerste kolom van de eerste swimlane. Zet "Opslaan als" op "Snippet",
    neem iets op en sla op → je komt op de Snippets-pagina met een nieuwe snippet
    (`notitie.txt`, platte tekst).
41. Ga naar Account → OpenAI API-sleutel en vul een ongeldige sleutel in (bv. `sk-test`),
    klik "Opslaan". Open het opnamepaneel, neem iets op, klik op "✨ Laat AI het type
    bepalen" → je krijgt een duidelijke foutmelding onder de knop (OpenAI wijst de sleutel
    af), geen crash. Wis de sleutel weer via "Sleutel wissen" en probeer de knop opnieuw →
    nu een andere, duidelijke foutmelding ("Stel eerst een OpenAI API-sleutel in..."). Vul
    een echte, werkende OpenAI-sleutel in en probeer het nogmaals met een duidelijke
    to-do-zin (bv. "ik moet morgen de auto laten wassen") → de "Opslaan als"-keuzelijst
    springt naar "Taak", de titel en tags worden voorgesteld, en er verschijnt een regel
    "AI denkt: taak '...' — controleer de velden en klik op ...". Klik daarna zelf op de
    "Opslaan als taak"-knop → de taak wordt pas nú aangemaakt, met de tekst zoals die op dat
    moment in het transcript-veld staat (dus als je die nog aanpast vóór het klikken, komt
    jouw aanpassing erin, niet wat de AI oorspronkelijk zag).
42. Maak een taak aan, ga naar Kanban en klik in een kolom op "+ Taak toevoegen" → je taak
    staat in de keuzelijst. Kies 'm en klik "Toevoegen" → de kaart verschijnt met een
    ✓-icoontje vóór de titel dat naar de bewerkpagina van de taak linkt, en dezelfde taak
    staat niet meer in de "+ Taak toevoegen"-keuzelijst (al gekoppeld). Klik op het
    ✎-icoontje naast een swimlane-naam, wijzig de naam en klik "Opslaan" → de kop van de
    swimlane toont meteen de nieuwe naam. Maak een tweede swimlane aan → er verschijnt nu
    een 🗑-icoontje bij beide swimlanes (bij precies één swimlane staat dat icoontje niet).
    Klik het 🗑-icoontje bij de nieuwe swimlane, bevestig → de swimlane en alles erin is weg.
    Probeer de allerlaatste overgebleven swimlane te verwijderen → dat lukt niet (foutmelding
    i.p.v. een leeg bord).
43. Open het opnamepaneel → onder de opnameknop staat "of upload een bestaand
    audiobestand". Kies een mp3/m4a-bestand van je computer → net als bij een eigen opname
    verschijnt na even wachten het transcript, bewerkbaar in het tekstvak. Klik op "📝
    Samenvatten met AI" (met een geldige OpenAI-sleutel ingesteld) → het transcript-tekstvak
    wordt vervangen door een beknopte samenvatting, met een regel eronder die dat bevestigt.
    Pas de samenvatting nog aan en sla op als notitie → de aangepaste samenvatting (niet het
    originele transcript) komt in de notitie terecht.
44. Maak een notitie en een snippet aan → de selectievakjes ervoor (bulk-select) zijn nu
    ronde, halftransparante cirkeltjes i.p.v. vierkante native checkboxes; aangevinkt vullen
    ze zich met de accentkleur op 50% dekking. Controleer ook dat de notitietitels in de
    lijst kleiner ogen dan voorheen. Ga naar Account → Weergave → Lettergrootte → er staan nu
    ook 11px en 12px in de keuzelijst (naast de bestaande 13–18px).
45. Klik op de ronde hub rechtsonder (het quick-add-wiel) → het wiel klapt open, merkbaar
    kleiner dan voorheen, met een egale donkere achtergrond en oranje gloed-rand — geen
    felgekleurde taartpunten meer. Open daarna Pomodoro (sidebar) → de kleuren/achtergrond
    van de Pomodoro-cirkel zien er hetzelfde uit als het wiel net.
46. Kijk naar het browsertabblad → het icoon is een oranje "P" op een antraciet
    afgeronde-vierkant-achtergrond, i.p.v. het generieke browser-standaardicoon.
47. Maak een taak aan en vink 'm af (afgerond). Zet in een database-tool (of via de Python-
    shell) `completed_at` van die taak 5 dagen terug en herlaad de takenlijst → de taak is
    weg. Maak nog een taak aan en zet z'n `updated_at` 8 dagen terug → de kaart krijgt een
    witte linkerrand en lichte witte tint. Wijzig de taak (bv. de titel) → de witte markering
    verdwijnt (updated_at is weer "nu").
48. Open Taken/Notities/Mindmap → de tag-filter-checkboxes bij "Tags:" zijn kleine ronde
    rondjes in de kleur van de tag, geen vierkante native checkboxes meer. Open Taken →
    Nieuwe taak → "Prioriteit"/"Dagtaak" zijn nu ook ronde vinkjes; zelfde bij Notities →
    Nieuwe notitie → "Tijdelijke notitie". Bewerk een kanban-kaart → de "Geen kleur"-checkbox
    bij de kleurkiezer is ook rond.
49. Genereer een API-token (Account → API-token) en doe (met een echt token, zonder
    sessie-cookie):
    ```bash
    curl -X POST http://localhost:8887/api/v1/kanban/swimlanes \
      -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
      -d '{"name": "Support"}'
    ```
    → 200 met de nieuwe swimlane-id en de 4 standaardkolommen (Backlog/Todo/In
    Progress/Done) in de JSON-response. Ga naar `/kanban` → de swimlane staat er, met
    dezelfde kolommen als een via de browser aangemaakte swimlane. Doe dezelfde aanroep
    zonder de `Authorization`-header → 401 i.p.v. de eerdere 303-redirect-naar-inlog van de
    gewone web-route.
50. Ga naar Taken → de sorteer-/tag-filter-controls zijn weg uit het standaardbeeld, alleen
    een "⚙ Filter & sorteren"-knop staat er nog. Klik erop → hetzelfde paneel (sorteren,
    groeperen, tags) klapt open. Filter op een tag en klap het paneel weer dicht → de knop
    toont nu een badge met het aantal actieve tag-filters. Zelfde check bij Notities
    (sorteren + tags, de raster/lijst-toggle blijft wel altijd zichtbaar).
51. Ga naar Kanban, klik het ✎-icoontje naast een swimlane-naam → het tekstveld met de
    huidige naam is nu volledig zichtbaar (niet meer afgesneden aan de rechterkant), en je
    kunt gewoon zien wat je intypt.
52. Maak een gewone taak aan (geen prioriteit) en een taak mét "Prioriteit" aangevinkt →
    onderaan elke pagina glijdt een donkere balk, maar alleen met de prioriteitstaak (★),
    de gewone taak staat er niet in. Klik op de taak in de balk → je komt op de
    bewerkpagina. Vink de prioriteitstaak af → die verdwijnt uit de balk (ververst pas bij
    een volgend paginabezoek, niet live). Klik het kruisje rechts in de balk → de balk
    verdwijnt en de quick-add-wheel/Pomodoro-knop schuiven een stukje omlaag; herlaad de
    pagina → de balk
    blijft verborgen.
53. Maak een nieuwe swimlane aan (of, op een verse installatie, kijk naar "Mijn bord") →
    de kolommen heten Backlog/To Do/In Progress/Review/Done (5 stuks). Tussen elke kolom
    staat een verticale stippenlijn die van kleur wisselt (roze, oranje, blauw, groen) met
    een zachte gloed eromheen die naar de achtergrond vervaagt.
54. Maak een snippet aan met een beschrijving en één bestand → op de kaart in de lijst zie
    je meteen de titel + "zojuist" rechtsboven, de beschrijving, tags (of "Geen tags"), en
    een live preview van het bestand met een bestandsnaam-balkje. Klik het kopieer-icoontje
    → de code staat op je klembord. Klik het uitklap-icoontje (of de titel) → hetzelfde
    bijna-volledig-scherm paneel als voorheen. Maak een tweede snippet aan zonder
    beschrijving en met 2 bestanden → de kaart toont "Geen beschrijving beschikbaar", het
    eerste bestand als preview, en een "+ 1 meer bestand"-knop die ook het volledige-scherm-
    paneel opent.
55. Ga naar Snippets → "⇅ Export / Import" → klik "Exporteren als JSON" → een `.json`-
    bestand met al je snippets wordt gedownload. Klik "Exporteren als Markdown" → een
    leesbaar `.md`-bestand met dezelfde inhoud. Upload het JSON-bestand weer via
    "Importeren (JSON)" → een melding "N snippet(s) geïmporteerd" verschijnt, en je hebt nu
    dubbele snippets (de import voegt toe, overschrijft niet). Probeer een willekeurig
    tekstbestand (geen geldige JSON) te importeren → een duidelijke foutmelding i.p.v. een
    kale foutpagina.
56. Maak een snippet aan met een bestand dat lange regels + veel regels heeft (genoeg om
    zowel horizontaal als verticaal te moeten scrollen in de preview) → de scrollbars zijn
    subtiel donkergrijs, niet de witte systeemstandaard. Wissel van thema naar "white" of
    "light" → de code-preview blijft donker (highlight.js' eigen kleurschema) en de
    scrollbar blijft er donkergrijs bij passen i.p.v. wit te worden.
57. Maak een kanban-kaart aan → de titel staat in hetzelfde oranje als "Productivity Suite"
    bovenaan de sidebar. Wissel van thema → de kaarttitel blijft exact datzelfde oranje
    (verandert niet mee met het thema's eigen accentkleur).
58. Maak een taak, notitie en snippet aan, elk met een tag, plus van elk ook één zonder tag
    → de tag-bubbels zelf zijn overal een volle kleur met witte tekst (geen lichte vulling
    + gekleurde rand meer). Zet het thema op "Bubbles" (laatste, regenboogkleurige swatch)
    → de taak-/notitie-/snippet-kaarten mét een tag krijgen nu ook een volle kleur (van die
    tag) met een zachte schaduw en geen rand; de kaarten zonder tag blijven een gewone
    neutrale kaart. Zet het thema terug naar bv. Dracula → alle kaarten zijn weer gewoon
    neutraal, ook die met een tag (de volle-kleur-kaart is uniek voor "Bubbles").
59. Ga naar Notities → nieuwe notitie → plak een afbeelding (bv. een screenshot) in het
    tekstvak → de afbeelding verschijnt meteen op de cursorpositie met afgeronde hoeken. Sla de
    notitie op → ga terug naar de lijst → de afbeelding staat (met dezelfde afgeronde hoeken)
    ook in de kaartpreview. Open de notitie opnieuw om te bewerken → de afbeelding staat er nog.
60. Vink een taak af en zet in de database `completed_at` meer dan 24 uur terug → de taak staat
    niet meer in de lijst maar wel onder Taken → Archief; "Herstellen" zet 'm terug. Kijk in
    `data/backups/` → een `app-<datum>.db` en `snippets/<id>.json` per snippet.
61. Kalender → "+ Afspraak" → kies Herhaling "Elke week" → opslaan: de afspraak staat met ↻ op
    elke week, en onder de kalender in het blok "Herhalende afspraken". Open 'm → "Herhaling
    stoppen" → latere weken zijn weg, eerdere blijven; het blok toont 'm niet meer.
62. Kanban → vink "Lanes standaard ingeklapt" aan → alle swimlanes klappen dicht en blijven dicht
    na verversen; klik een lane-naam om 'm tijdelijk open te klappen; vinkje uit → de eerder
    onthouden open/dicht-stand per lane geldt weer.
63. Sidebar → Stickies → typ een tekst, kies roze, tags "werk", vink Temp aan → Toevoegen: het
    briefje staat roze met TEMP-label en tag. Klik een andere kleur op een briefje → het
    wisselt meteen en blijft zo na verversen. Klik een tag → alleen stickies met die tag.

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
- **BUGFIX/stijlkeuze — tag-bubbels in een volle kleur i.p.v. lichte vulling + rand**: een
  tag-badge (`.tag[style*="--tag-hue"]` in `app.css`) had eerst een lichte, 25%-transparante
  vulling met een duidelijk gekleurde rand en de gewone (thema-afhankelijke) tekstkleur —
  nu een volle, solide achtergrondkleur (`hsl(hue, 65%, 42%)`) zonder rand, met altijd witte
  tekst. Dit geldt bewust alléén voor tags mét een geldige hue (dus een echte kleur); een
  tag zonder hue (`badge_style` dan leeg, bv. een oude/handmatige hex-kleur) valt terug op
  de gewone `.tag`-achtergrond/tekstkleur, nooit op geforceerd wit — zo kan "wit-op-wit"
  hier niet ontstaan.
- **"Bubbles"-thema: volle tag-kleur ook op taak-/notitie-/snippet-kaarten**: een nieuw
  thema (Account → Weergave → thema-zwaaitjes, laatste swatch) dat taak-, notitie- en
  snippet-kaarten met een tag een volle achtergrondkleur geeft (van de eerste tag, net als
  de tag-bubbel zelf) met een zachte schaduw i.p.v. een rand — kaarten zonder tag blijven
  een gewone, neutrale kaart. Nieuwe `Task.row_tint_style`/`Note.row_tint_style`
  (`Snippet.row_tint_style` bestond al, hergebruikt nu dezelfde gedeelde helper
  `app/services/tags.py::first_tag_hue_style`) zetten `--tag-hue` als CSS custom property
  op de kaart; de standaard-thema's doen daar niets zichtbaars mee (geen ongevraagde
  kleurtint op taken/notities in andere thema's), alleen `themes/bubbles.css` leest 'm om
  er een volle kleur van te maken. Snippet-kaarten hadden al langer een lichte 8%-tint op
  basis van dezelfde `--tag-hue`-variabele (nu scoped tot alléén `.snippet-card`, niet
  task-/note-card) — die blijft in alle andere thema's ongewijzigd.
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
- **Notities-editor — geplakte afbeeldingen**: een `paste`-listener op de editor onderschept
  clipboard-items van het type `image/*`, leest ze via `FileReader.readAsDataURL` uit en voegt
  het resultaat in als `<img src="data:...">` op de cursorpositie (`document.execCommand
  insertImage`) — bewust geen losse upload-route/static-map, de afbeelding leeft gewoon als
  base64 in de notitie-HTML zelf, consistent met de rest van deze app (één SQLite-bestand, geen
  extra infrastructuur). Trade-off: de opgeslagen notitie wordt ~33% groter dan de binaire
  afbeelding, acceptabel voor een persoonlijke single-user app. `sanitize_note_html` staat
  `img[src,alt]` toe en laat naast `http`/`https`/`mailto` ook het `data`-schema door bij
  `bleach.clean` — dat geldt voor alle URL-dragende attributen die bleach herkent (dus ook
  `a[href]`), een bewust aanvaarde verruiming gezien het single-user, self-hosted dreigingsmodel
  van deze app. CSS (`'.rich-editor img', '.note-card-preview img'`) rondt de hoeken af en
  begrenst de breedte zodat een grote geplakte afbeelding de editor/kaart niet opblaast.
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
- **Snippets — bijna-volledig-scherm viewer i.p.v. inline uitklappen**: de code
  (`.snippet-files`) staat per kaart standaard `hidden` en blijft dat ook — dit is nu puur de
  *bron*, niet meer wat er getoond wordt. Een klik op de titel (`app/static/js/snippets-list.js`)
  kloont die verborgen node (`cloneNode(true)`) in een los modal-paneel (`inset: 3vh 3vw`) i.p.v.
  'm inline te tonen; de kloon is nodig zodat `hljs.lineNumbersBlock()` (de
  highlightjs-line-numbers.js-plugin, CDN, geen aparte CSS nodig — de `.hljs-ln*`-klassen zijn
  handmatig gestyled in `app.css` zodat ze in elk thema passen) niet twee keer op dezelfde node
  toegepast wordt als je 'm meerdere keren opent. `hljs.highlightAll()` verwerkt de
  code-blokken sowieso bij het laden van de pagina (ook terwijl ze verborgen zijn — highlight.js
  werkt op de DOM, niet op wat er zichtbaar is), dus de kloon erft die opmaak al mee en hoeft
  zelf niet opnieuw gehighlight te worden.
- **Snippets — code bewerken vanuit de viewer, los van het volledige bewerkformulier**: een
  nieuwe, bewust smalle route (`POST /snippets/{id}/files/{file_id}/content`, alleen een
  `content`-form-veld) werkt alléén de inhoud van dat ene bestand bij — title/tags/overige
  bestanden blijven gegarandeerd ongemoeid, in tegenstelling tot de bestaande
  `update_snippet`-route die de hele bestandenlijst + titel + tags in één keer vervangt
  (`_apply_files_from_form`) en dus een leeg meegestuurd titel/tags-veld per ongeluk zou
  kunnen laten leeglopen. "Bewerken" in het fullscreen-paneel vervangt per bestand de
  `<pre><code>` door een `<textarea>`. Een addertje onder het gras: `hljs.lineNumbersBlock()`
  herstructureert de code in een `<table>` per regel, waarbij de originele `\n`-tekens
  verdwijnen (regeleinden worden dan tabelrijen i.p.v. tekens) — `codeEl.textContent`
  opvragen ná het toepassen van regelnummers levert dus alle regels aan elkaar geplakt op.
  Fix: de platte tekst wordt vóór het toepassen van regelnummers weggeschreven naar
  `codeEl.dataset.rawContent`, en de textarea leest daaruit i.p.v. uit `textContent`.
  "Opslaan" stuurt élk bestand als losse fetch-call weg en herlaadt de pagina bij succes
  (simpel en consistent met de rest van de app, die overwegend op page-navigaties leunt
  i.p.v. een SPA-aanpak); "Annuleren" rendert de viewer gewoon opnieuw vanuit de nog
  onaangeraakte bron-node, dus zonder network-call.
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
  iteraties die dat wel hadden) — het enige JS is het open/dicht togglen van het wiel. Elke
  `.quickadd-spoke` staat gepositioneerd via een vooraf berekende `translate(x, y)`
  (trigonometrie op 72°-intervallen vanuit het midden) i.p.v. `sin()`/`cos()` in CSS, voor
  bredere browserondersteuning. `.quickadd-wheel-wrap` is 45×45px als het wiel dicht is (hub
  plakt in de hoek) en 210×210px als het open is (30% kleiner dan de oorspronkelijke
  64px/300px) — de hub zelf is altijd gecentreerd in die wrapper
  (`top:50%;left:50%;transform:translate(-50%,-50%)`), dus schuift vanzelf mee van de hoek
  naar het midden van het opengeklapte wiel, zonder dat de hub zelf een aparte
  positie-berekening nodig heeft. **BUGFIX/stijlkeuze**: de taartpunten hadden eerst 6
  losse felle kleuren via één `conic-gradient` (letterlijk een "pizza"-look) — vervangen
  door dezelfde egale donkere-glas-achtergrond + oranje gloed-rand als de
  Pomodoro-widget (`.pomodoro-circle`), voor een consistente stijl-taal tussen de twee
  zwevende widgets i.p.v. twee losse ontwerpen.
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
- **Tags weg uit de overzichten, wel in het edit-scherm**: de tag-badges op notitiekaarten
  (raster/lijst) en kanban-kaarten (bord) zijn verwijderd om ruimte te besparen bij veel
  items in één overzicht — de bestaande tag-filter (notities) en het tags-veld in het
  bewerkformulier/-modal blijven de manier om tags te zien/wijzigen. De onderliggende
  tag-koppelingen en de gedeelde-tag-infrastructuur (`resolve_tags`, `badge_style`, de
  Graph-pagina) zijn ongewijzigd — dit is puur een weergavewijziging.
- **BUGFIX — `PRAGMA foreign_keys=ON` (`app/database.py`)**: bij het bouwen van de
  bovenstaande wijziging bleek dat SQLite `ondelete="CASCADE"`/"SET NULL" op
  ForeignKey-kolommen (overal in `app/models/*.py`) gewoon **negeert** tenzij
  foreign-key-afdwinging per connectie expliciet wordt aangezet. Zonder deze pragma liet
  een bulk-delete (`Query.delete()`, dat buiten de ORM-cascade om gaat — bv.
  `bulk_delete_notes` en het opruimen van verlopen tijdelijke notities) een rij in de
  tag-koppeltabel (`note_tags` e.d.) achter nadat het getagde item al weg was. Zodra SQLite
  later hetzelfde primary-key-id hergebruikte voor een nieuwe, ongerelateerde rij (normaal
  gedrag bij een INTEGER PRIMARY KEY zonder AUTOINCREMENT), "erfde" die nieuwe rij per
  ongeluk de oude tags — precies zo ontdekt tijdens het handmatig testen van deze feature.
  Nu wordt de pragma bij elke connectie gezet (`event.listens_for(engine, "connect")`), én
  ruimt `app/services/migrate.py::_cleanup_orphaned_tag_associations` bij elke start
  eenmalig eventuele al bestaande wees-rijen op (voor installaties die deze bug al
  hebben meegemaakt vóór deze fix).
- **Whisper/Speaches: per-gebruiker DB-instelling i.p.v. alleen env vars**: `User.
  whisper_service_url`/`whisper_model` (nullable, `None` = val terug op de
  WHISPER_SERVICE_URL/WHISPER_MODEL-env vars uit `app/config.py`). Zowel
  `POST /voice/transcribe` als de nieuwe `POST /voice/test-connection` gebruiken dezelfde
  `_resolve_whisper_config(user, url_override, model_override)`-helper, met als
  prioriteitsvolgorde: het formulierveld (nog niet opgeslagen, voor "test vóór opslaan") →
  de opgeslagen per-gebruiker instelling → de env var/app-default. De verbindingstest
  bevraagt `GET {url}/v1/models` (Speaches' OpenAI-compatibele modellenlijst) i.p.v. alleen
  te checken of de service reageert — zo zie je ook meteen of het ingestelde model daar
  wel/niet bij staat, in plaats van pas te ontdekken dat het misgaat bij de eerste
  opname.
- **Snippets bulk-delete: routevolgorde-valkuil**: `POST /snippets/bulk-delete` gaf eerst
  een 422 i.p.v. te werken, omdat FastAPI/Starlette routes in registratievolgorde matcht en
  de generieke `POST /snippets/{snippet_id}` (van `update_snippet`) al eerder geregistreerd
  stond — "bulk-delete" werd dan als `snippet_id` geprobeerd te parsen (faalt, want geen
  getal) i.p.v. de bedoelde route te raken. Fix: de specifieke `/bulk-delete`-route moet vóór
  de generieke `/{snippet_id}`-routes geregistreerd staan (dezelfde volgorde-eis gold al voor
  `/notes/bulk-delete` in `app/routers/notes.py` — dit keer bij het toevoegen aan snippets
  over het hoofd gezien en tijdens het testen gevonden).
- **Voice-opname vereist een secure context**: `navigator.mediaDevices.getUserMedia` (het
  microfoon-API van de browser) werkt alleen op `https://` of `http://localhost` — niet op
  gewoon `http://<ip-adres>:poort`, wat voor een self-hosted app op het lokale netwerk (bv.
  Unraid zonder reverse proxy) juist de normale manier van toegang is. Zonder HTTPS geeft
  de browser altijd "Kon geen toegang krijgen tot de microfoon", ongeacht of de gebruiker
  toestemming zou geven — dit is browserbeleid, geen bug in de app. Oplossingen: een reverse
  proxy met een certificaat vóór de app zetten (structureel, voor iedereen), of per browser
  het adres als "secure" whitelisten via een instelling als
  `chrome://flags/#unsafely-treat-insecure-origin-as-secure` (`edge://flags/...` in Edge,
  Chromium-gebaseerde browsers delen dezelfde vlag) — een snelle workaround per apparaat,
  geen serverwijziging nodig.
- **`/voice/transcribe` — taal expliciet kunnen meegeven**: `language` is een optioneel
  form-veld (leeg = Whisper's eigen taaldetectie). Vooral het "tiny"-model detecteert de
  taal bij korte spraakfragmenten onbetrouwbaar (soms zelfs binnen één opname wisselend) —
  een taal-keuzelijst in de UI (`app/templates/base.html`, onthouden in `localStorage`)
  stuurt 'm als form-veld mee naar Speaches, dat 'm doorzet naar faster-whisper's eigen
  `language`-parameter.
- **Zoeken (`app/routers/search.py`) — losse queries per entiteit i.p.v. één generieke
  tabel**: er is bewust geen gedeelde "doorzoekbare items"-tabel/view gebouwd — elk van de
  zes taggable modellen (Task, Note, KanbanCard, Snippet, MindmapBoard, CalendarEvent) heeft
  eigen tekstvelden en een eigen relatie naar `user_id` (`KanbanCard` alleen indirect, via
  een join op `KanbanBoard`), dus `/search` doet zes losse, user-gescoopte queries met
  `ILIKE`/`Tag.name`-filters i.p.v. één generieke abstractie — dat past beter bij hoe de rest
  van de app per entiteit is opgebouwd, en blijft simpel zolang het er zes blijven. De
  tag-keuzelijst op de zoekpagina toont alle tags in het systeem (`db.query(Tag)` zonder
  filter), niet per-gebruiker — `Tag` heeft bewust geen `user_id`-kolom (zie de
  Kanban-bugfix hierboven over gedeelde tag-infrastructuur), en voor een
  single-user-per-deployment app is dat geen probleem. Kanban-kaarten hebben geen eigen
  bewerkpagina (ze worden inline op het bord bewerkt), dus die zoekresultaten linken naar
  `/kanban` in plaats van naar een specifieke kaart.
- **Kalender-als-startpagina bestond al, geen aparte instelling nodig**: `GET /` in
  `app/main.py` stuurt een ingelogde gebruiker altijd door naar `/calendar` (zie de
  Kalender-bugfix/architectuurnotitie eerder in dit bestand) — dit was dus al zo vóórdat de
  zoekfunctie werd toegevoegd.
- **Voice fase 2 (`POST /voice/classify`) hergebruikt de bestaande create-routes, geen eigen
  opslaglogica**: het endpoint doet zelf niets met de database -- het geeft alleen
  `{type, title, tags}` terug aan de browser, die daarmee dezelfde `/tasks`-, `/notes`-,
  `/kanban/cards`- en `/snippets`-routes aanroept die ook de handmatige "Opslaan als"-flow
  (fase 1) en de agent-API al gebruiken. Zo blijft er precies één plek per entiteit die
  weet hoe een taak/notitie/kaart/snippet aangemaakt wordt. De classificatieprompt vraagt
  bewust NIET om de inhoud te herschrijven (alleen type/titel/tags) -- de inhoud is en
  blijft het transcript dat de gebruiker al gecontroleerd heeft; een tweede AI-laag die de
  tekst zelf ook nog aanpast zou een tweede plek zijn waar het mis kan gaan, boven op de
  spraakherkenning zelf.
- **Kanban-kaart vanuit voice: eerste cel, geen keuze-UI**: `GET /kanban/default-cell`
  (`app/routers/kanban.py`) geeft de eerste swimlane/kolom van het bord terug. Er is bewust
  geen los stap in het voice-paneel om een swimlane/kolom te kiezen (dat zou het paneel
  onnodig complex maken voor een functie die je terloops via spraak gebruikt) -- de kaart
  komt in de eerste cel terecht en is daarna via drag-and-drop net zo makkelijk te
  verplaatsen als elke andere kaart.
- **`gpt-4o-mini` hardcoded i.p.v. instelbaar**: in tegenstelling tot Whisper (waar het
  model wél instelbaar is, omdat verschillende self-hosted Speaches-installaties andere
  modellen geladen kunnen hebben) is er voor de OpenAI-classificatie geen instelbaar model
  -- dit is een simpele, goedkope classificatietaak (geen lange generatie) waarvoor één
  vast klein model volstaat, en instelbaarheid zou hier alleen maar een extra
  foutbron/instelling toevoegen zonder echt voordeel.
- **BUGFIX — taak-op-bord kopieert eenmalig, geen live-sync**: `KanbanCard.task_id` bestond
  al in het model (`ondelete="SET NULL"`) maar werd nergens gezet -- er was dus geen manier
  om een bestaande taak op het bord te zetten, alleen een losse kaart met dezelfde tekst
  opnieuw intypen. `POST /kanban/cards/from-task` (`app/routers/kanban.py`) kopieert
  titel/beschrijving/tags op het moment van toevoegen; wijzig je de taak daarna, dan wijzigt
  de kaart niet automatisch mee (en andersom). Een levende sync zou een aparte
  achtergrondsync of een joined weergave vereisen -- bewust niet gebouwd, want dit is een
  persoonlijke app zonder scheduler/achtergrondproces (zie ook de tijdelijke-notities-notitie
  hieronder over dezelfde "geen cron"-keuze). De takenkeuzelijst per cel toont alleen
  niet-afgeronde taken die nog niet aan een kaart gekoppeld zijn (`board_view` in
  `app/routers/kanban.py`), zodat je een taak niet twee keer per ongeluk toevoegt.
- **BUGFIX — swimlane/kolom verwijderen faalde op een NOT NULL-constraint**: `KanbanCard`
  heeft niet-nullable `column_id`/`swimlane_id`-kolommen met `ondelete="CASCADE"` op de FK
  (en `PRAGMA foreign_keys=ON`, zie de eerdere tag-cascade-bugfix hieronder). Zonder meer
  probeerde SQLAlchemy bij het verwijderen van een swimlane/kolom éérst zelf de kaarten hun
  `column_id`/`swimlane_id` op `NULL` te zetten (standaardgedrag als een relationship geen
  cascade-optie heeft), wat botst met de NOT NULL-kolom en een `IntegrityError` gaf.
  Opgelost met `passive_deletes=True` op `KanbanColumn.cards`/`KanbanSwimlane.cards`
  (`app/models/kanban.py`): dat zegt tegen SQLAlchemy "beheer deze kant niet zelf, vertrouw
  op de databasecascade", die de kaarten (en via `card_tags` ook de tag-koppelingen) gewoon
  laat meeverwijderen.
- **Laatste swimlane van een bord kun je niet verwijderen**: zonder deze check zou je een
  bord kunnen leegmaken tot nul swimlanes, waarna er nergens meer een "+ Kaart
  toevoegen"-cel is om zonder omweg (eerst een nieuwe swimlane aanmaken) verder te gaan --
  een simpele `len(board.swimlanes) <= 1`-check in `delete_swimlane` voorkomt dat, met een
  duidelijke 400-foutmelding i.p.v. een verwarrend leeg bord.
- **Bestand uploaden hergebruikt `/voice/transcribe` zonder aanpassing**: een `<input
  type="file">` in het opnamepaneel stuurt het gekozen bestand naar dezelfde route als een
  eigen `MediaRecorder`-opname (`transcribeBlob()` in `app/static/js/voice.js`, gedeeld
  tussen beide paden) -- Speaches/de OpenAI Audio API maakt geen onderscheid tussen "audio
  van de microfoon" en "audio van schijf", dus was er geen backend-wijziging nodig, alleen
  een nieuwe manier om aan de audio-bytes te komen in de browser.
- **`/voice/summarize` en `/voice/classify` delen nu één `_openai_chat_completion()`-helper**
  (`app/routers/voice.py`): zelfde model, sleutel-check, foutafhandeling -- alleen de
  prompt/berichten en (bij classificeren) de JSON-`response_format` verschillen. Voorkomt
  dat een toekomstige derde AI-functie (bv. de nog-niet-gebouwde mindmap-generatie) die
  hele httpx/foutafhandelingsblok opnieuw moet kopiëren.
- **Samenvatten vervangt het transcript-veld, geen apart samenvatting-veld**: bewust geen
  losse "samenvatting"-textarea naast het transcript -- dat zou een keuze toevoegen
  ("welke van de twee sla ik nu op?") die de bestaande, al begrepen bevestigingsstap
  (één bewerkbaar tekstvak, wat erin staat wordt opgeslagen) alleen maar verwart. Wie de
  samenvatting niet wil, negeert de knop gewoon; wie 'm niet meer wil nadat die is
  toegepast, neemt het transcript opnieuw op/upload het opnieuw.
- **Ronde checkboxes door de hele app heen i.p.v. vierkant**: begon bij `.note-select`/
  `.snippet-select` (bulk-select), later doorgetrokken naar **alle** checkboxes in de app.
  `appearance: none` + een eigen cirkelvormige `border-radius: 50%`-styling (zelfde patroon
  als `.task-check`, dat al langer rond was), met `color-mix(in srgb, var(--accent) 50%,
  transparent)` als gevulde kleur zodra aangevinkt. Een nieuwe gedeelde class
  `.round-checkbox` (`app/static/css/app.css`) staat nu op de losse formulier-checkboxes
  (taak-Prioriteit/Dagtaak, notitie-Tijdelijk, kanban-kaart-"Geen kleur") — `.note-select`/
  `.snippet-select` bleven hun eigen classnaam houden (JS gebruikt die als hooks voor
  bulk-acties) maar delen dezelfde CSS-regel via een gecombineerde selector, i.p.v. de
  stijl te dupliceren. De kleine tag-filter-checkboxes (`.tag-checkbox input`, in taken/
  notities/mindmap) kregen een eigen, kleinere ronde variant die `currentColor` gebruikt
  i.p.v. de vaste accentkleur, zodat het rondje de kleur van de tag zelf overneemt (past
  bij de per-tag-kleur die de omliggende pil-badge al had via `badge_style`).
- **`Task.completed_at` apart van `updated_at`**: `updated_at` verandert bij élke wijziging
  (titel, tags, deadline, ...), dus die alleen gebruiken zou een taak die je ná het afronden
  nog even bewerkt telkens weer 4 dagen "vers" maken. `completed_at` wordt alleen gezet/
  gewist bij een status-overgang van/naar 'done' (via de gedeelde `_apply_status()`-helper
  in `app/routers/tasks.py`, gebruikt door zowel het bewerkformulier als de
  snel-afvink-knop, zodat er geen tweede plek is die dat kan vergeten). Bestaande, al vóór
  deze kolom afgeronde taken krijgen bij de eerstvolgende opstart een benaderde
  `completed_at` via een backfill-migratie (`_backfill_completed_at` in
  `app/services/migrate.py`, `completed_at = updated_at` voor alle 'done'-taken zonder
  completed_at) — anders zouden die nooit opgeruimd worden, want `NULL < cutoff` is in
  SQLite altijd onwaar.
- **`Task.stale` kijkt naar `updated_at`, niet naar `completed_at`**: bewust twee losse
  concepten — "al een tijdje niet aangeraakt" (stale, 7 dagen, elke status) is iets anders
  dan "al een tijdje geleden afgerond" (opruimen, 4 dagen, alleen 'done'). Een net
  aangemaakte, nog niet afgeronde taak die je een week laat liggen moet wél als stale
  opvallen, ook al is-ie nooit "done" geweest.
- **BUGFIX — swimlane aanmaken kon niet via de agent-API**: de web-route
  `POST /kanban/swimlanes` bestond al veel langer, maar was nooit als `/api/v1/...`-endpoint
  ontsloten (alleen taken/kaarten/notities/snippets waren dat) — een extern script/agent kon
  dus geen swimlane aanmaken zonder een browser-sessie te faken, wat met een los API-token
  sowieso niet kan (de web-routes controleren op de sessie-cookie, niet op
  `Authorization: Bearer`). Nieuwe `POST /api/v1/kanban/swimlanes`
  (`app/routers/api.py`) met dezelfde `require_api_user`-afhankelijkheid als de rest van de
  agent-API, en dezelfde logica als de web-route (nieuwe swimlane krijgt de
  standaardkolommen uit `app/services/seed.py::DEFAULT_COLUMNS`).
- **`.filter-panel` als gedeelde `<details>`-wrapper (Taken/Notities)**: bewust een gewone
  `<details>`/`<summary>` i.p.v. een JS-gestuurd dropdown-paneel (zelfde patroon als
  "+ Kaart toevoegen" op het kanbanbord) -- geen extra JS nodig voor open/dicht-gedrag, en
  het klapt in-flow open (duwt de rest van de pagina naar beneden) i.p.v. als overlay, wat
  het risico op de "valt buiten beeld"-bug hieronder bij de swimlane-rename vermijdt. De
  badge (`.filter-panel-badge`) telt alleen actieve tag-filters -- sorteren/groeperen zijn
  geen "filters" in de zin dat ze items verbergen, dus die tellen bewust niet mee.
- **BUGFIX — swimlane-hernoem-popup viel buiten beeld**: `.swimlane-rename-form form` had
  `left: 0`, wat de popup naar rechts liet groeien vanaf een ✎-icoontje dat door
  `flex: 1` op `.swimlane-toggle` al helemaal rechts in de (mogelijk brede, horizontaal
  scrollbare) swimlane-kop stond -- op smallere/gescrollde boards viel het tekstveld
  daardoor grotendeels of helemaal buiten het zichtbare scherm. Nu `right: 0` (groeit naar
  links, richting reeds-zichtbare inhoud) plus een vaste `width: 150px` op het tekstveld
  zelf (zonder expliciete breedte kon een flex-child in een ongeclipte popup alsnog te
  smal renderen om iets van de getypte tekst te tonen).
- **Nieuws-ticker (`app/static/js/ticker.js`, `GET /tasks/ticker`)**: de inhoud staat
  dubbel achter elkaar (`#task-ticker-content` + een identieke `-dup`-kopie) en de
  CSS-animatie schuift precies 50% van de totale breedte op -- zodra de eerste kopie
  volledig van beeld is verdwenen, staat de tweede (identieke) kopie exact op de plek waar
  de eerste begon, wat een naadloze, oneindige lus geeft zonder zichtbare sprong bij het
  herstarten. De animatieduur schaalt licht mee met het aantal taken
  (`Math.max(20, Math.min(120, tasks.length * 4)) * 1.1` seconden -- de `* 1.1` is een losse
  "10% langzamer"-correctie bovenop de basisformule, op verzoek toegevoegd) zodat de band
  niet te snel voorbijflitst bij weinig taken en niet eeuwig duurt om rond te komen bij heel
  veel taken. De feed zelf (`GET /tasks/ticker`) geeft bewust alleen taken met "Prioriteit"
  aangevinkt terug, niet alle open taken -- anders zou de band bij een volle takenlijst al
  snel te druk/lang worden om nog een nieuwsband-gevoel te geven.
  De ticker en de zwevende widgets (quick-add-wheel, Pomodoro) houden elkaar in de gaten via
  een CSS-only `body:has(#task-ticker[hidden])`-selector i.p.v. een JS-klasse op `<body>` --
  scheelt een stukje coördinatie-JS tussen losse scripts (`ticker.js` weet niets van
  `quickadd.js`/`pomodoro.js` en andersom).
- **`DEFAULT_COLUMNS` uitgebreid naar 5, niet met terugwerkende kracht**: `app/services/
  seed.py::DEFAULT_COLUMNS` is een lijst die alleen gebruikt wordt op het *moment van
  aanmaken* van een swimlane (nieuwe installatie, "+ Swimlane toevoegen", of via de
  agent-API) -- er is bewust geen migratie die bestaande swimlanes op oudere installaties
  een "Review"-kolom erbij geeft, want dat zou ongevraagd de layout van een al ingericht
  bord veranderen. Wie dat alsnog wil, voegt 'm zelf toe via "+ Kolom" op de betreffende
  swimlane.
- **Kolom-dividers als losse elementen i.p.v. CSS `::before` op `.column` zelf**: elke
  divider is een eigen `<div class="column-divider column-divider-N">` tussen twee
  `.column`-elementen in de kolommenrij (`app/templates/kanban/board.html`), N =
  `(loop.index0 - 1) % 4` (cyclet door 4 kleuren, dus bij meer dan 5 kolommen in één
  swimlane herhaalt de kleurvolgorde vanaf roze). Bewust géén absoluut gepositioneerd
  pseudo-element op de kolom zelf (bv. `.column::before`) -- dat zou de dotted-line +
  gradient-gloed buiten de kolomgrenzen moeten laten overlappen op een naburige kolom, wat
  precies het soort positionerings-/z-index-gedoe is waar de swimlane-hernoem-popup-bugfix
  hierboven al tegenaan liep. Een gewoon flex-sibling-element met een eigen breedte (24px)
  is voorspelbaar en heeft geen last van overlap-issues.
- **Snippet-kaart: eerste bestand blijft "hidden" delen met de fullscreen-clone**: `#snippet-
  files-<id>` is niet langer zelf `hidden` (de kaart toont juist een live preview), maar elk
  `.snippet-file`-blok daarbinnen behalve het eerste heeft dat attribuut nog wel, zodat de
  kaart alleen het eerste bestand toont. `renderView()` in `snippets-list.js` kloont die hele
  container voor het volledige-scherm-paneel en verwijdert daar expliciet `hidden` van alle
  bestanden (`clone.querySelectorAll(".snippet-file[hidden]")...removeAttribute("hidden")`)
  — zonder die stap zouden bestand 2+ nooit zichtbaar worden in dat paneel, want ze zouden
  het `hidden`-attribuut van de kaart-bron meekopiëren.
- **`.snippet-toggle` is nu een kale functionele reset-class, geen visuele stijl**: staat
  inmiddels op drie verschillend gevormde knoppen (titel, uitklap-icoontje, "+ N meer
  bestanden") die alle drie hetzelfde volledige-scherm-paneel openen maar er heel anders
  uitzien — de daadwerkelijke vormgeving zit op specifiekere classes
  (`.snippet-card-title-btn`/`.snippet-expand-btn`/`.snippet-card-more-files`). De titel
  wordt niet meer uit een `.snippet-card-title-text`-childnode gelezen (dat bestaat niet in
  de andere twee knoppen) maar uit een `data-snippet-title`-attribuut dat op alle drie staat.
- **`Snippet.description` nieuw, optioneel veld**: toegevoegd om de ByteStash-look na te
  bootsen (die toont altijd een beschrijving, met "No description available" als
  placeholder) -- bestond hiervoor niet op het model. Additive migratie
  (`app/services/migrate.py`), dus bestaande snippets krijgen gewoon een lege beschrijving
  totdat je 'm zelf invult via "Bewerken".
- **Snippets-export/import is bewust snippet-only, geen deel van de hele-database-backup**:
  `GET /snippets/export` en `POST /snippets/import` (`app/routers/snippets.py`) draaien
  volledig los van Account → Backup (die exporteert/importeert de hele SQLite-database als
  `.db`-bestand). Het JSON-exportformaat bevat bewust geen database-id's (`{title,
  description, tags, files: [{filename, language, content}]}`), zodat een import niet kan
  botsen met bestaande id's en ook werkt als je 'm naar een andere installatie overzet.
  Markdown-export is puur voor lezen/delen (geen vaste, herimporteerbare structuur) -- er is
  dan ook bewust geen markdown-import gebouwd.
