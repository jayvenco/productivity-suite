# Backlog

Losse ideeën/wensen die (nog) niet ingepland zijn in een fase. Geen garantie op
volgorde — gewoon een geheugensteun voor later.

~~**Zoeken op tags**~~ — opgelost: de takenlijst heeft nu aanklikbare tag-checkboxes
waarmee je op meerdere tags tegelijk kunt filteren (OR-logica).

~~**Achtergronden-systeem**~~ — opgelost: Account → Weergave heeft nu een achtergrondkeuze
(Geen/Natuur/Bergen/Heelal) met een sterkte-schuifje. Gekozen voor drie vaste, self-hosted
foto's i.p.v. een live externe API — geen netwerkafhankelijkheid, in lijn met de rest van de
app. Meer categorieën/foto's toevoegen kan later alsnog als daar behoefte aan is.

~~**API voor externe agents/automatisering**~~ — opgelost: `/api/v1/tasks`,
`/api/v1/kanban/cards`, `/api/v1/notes` en `/api/v1/snippets` (JSON in/uit), beveiligd met
een los API-token (Account → API-token) i.p.v. de sessie-cookie. Scope bewust beperkt tot
*aanmaken* (geen lijst/bewerk/verwijder-endpoints) — dat kan later alsnog als daar behoefte
aan is.

~~**Backup/export-import**~~ — opgelost: Account → Backup, hele database in één `.db`-bestand
(via `VACUUM INTO`, dus veilig naast een lopende app), met automatische veiligheidskopie en
schema-update bij het importeren van een oudere back-up.

~~**Voice-opname → taken/notities/etc. (Whisper + ChatGPT)**~~ — opgelost (fase 1 én 2):

Fase 1: een 🎤 "Voice"-spaak in het quick-add-wiel opent een opnamepaneel (`MediaRecorder`
in de browser). Het audiofragment gaat naar `POST /voice/transcribe`
(`app/routers/voice.py`), dat 'm doorstuurt naar een **losse, zelf-gehoste Speaches-container**
(voorheen faster-whisper-server; `WHISPER_SERVICE_URL` + `WHISPER_MODEL` — bewust niet de
betaalde OpenAI Whisper-API, en niet ingebakken in de hoofd-image, zie README →
Architectuur). Het transcript verschijnt bewerkbaar in een tekstvak (de bevestigingsstap).
Je kiest zelf het type (Notitie/Taak/Kanban-kaart/Snippet) via "Opslaan als", met een eigen
tags-veld.

Fase 2: een "✨ Laat AI het type bepalen"-knop stuurt het transcript naar `POST
/voice/classify` (`app/routers/voice.py`), die ChatGPT (structured JSON-output) laat
bepalen welk type het moet worden + een titel + tags voorstelt. Bewust **alleen**
type/titel/tags — de inhoud blijft het transcript dat je net zelf gecontroleerd hebt, geen
tweede laag AI-herschrijving boven op de spraakherkenning. Het resultaat vult de velden
("Opslaan als" + titel + tags) alvast in, maar je klikt zelf nog op de "Opslaan als
..."-knop — dát is de bevestigingsstap, in plaats van een apart bevestigingsscherm. Vereist
een ingestelde OpenAI-sleutel (Account → OpenAI API-sleutel). Kanban-kaarten komen in de
eerste cel van het bord terecht (`GET /kanban/default-cell`) — er is geen UI om vanuit
voice een specifieke cel te kiezen, maar de kaart is daarna gewoon te verslepen.

**Nog niet gebouwd (mocht daar ooit behoefte aan zijn)**: matchen op een al bestaand item
i.p.v. altijd een nieuw item aanmaken (bv. "voeg dit toe aan mijn boodschappenlijst-notitie"
i.p.v. een nieuwe notitie).
