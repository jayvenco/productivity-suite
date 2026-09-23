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

**Voice-opname → taken/notities/etc. (Whisper + ChatGPT) — fase 1 opgelost, fase 2 nog niet**:

~~Fase 1~~ — opgelost: een 🎤 "Voice"-spaak in het quick-add-wiel opent een opnamepaneel
(`MediaRecorder` in de browser). Het audiofragment gaat naar `POST /voice/transcribe`
(`app/routers/voice.py`), dat 'm doorstuurt naar een **losse, zelf-gehoste Whisper-container**
(`WHISPER_SERVICE_URL`, standaard `ahmetoner/whisper-asr-webservice` — bewust niet de
betaalde OpenAI Whisper-API, en niet ingebakken in de hoofd-image, zie README →
Architectuur). Het transcript verschijnt bewerkbaar in een tekstvak (de bevestigingsstap)
en wordt bij "Opslaan als notitie" altijd als gewone notitie opgeslagen
(hergebruikt de bestaande `/notes`-route). Een OpenAI API-sleutel is al instelbaar via
Account → OpenAI API-sleutel, klaar voor fase 2.

**Fase 2 (nog te bouwen)**: de tekst laten interpreteren door ChatGPT (structured
output/JSON: welke actie — taak/notitie/kanban-kaart/snippet, evt. verwijzend naar een
bestaand item — met welke velden) i.p.v. altijd een notitie. De uitvoering hergebruikt de
bestaande create-routes/services (dezelfde die de agent-API al gebruikt), dus geen herbouw
van de kernlogica nodig — vooral een nieuwe interpretatie-stap + een eigen
bevestigingsscherm ("Ik heb begrepen: taak 'X' aanmaken — klopt dat?") vóór het écht wordt
uitgevoerd, want AI-interpretatie gaat af en toe mis. Kosten: verwaarloosbaar voor
persoonlijk gebruik (een kleine ChatGPT-prompt per commando; transcriptie zelf is al gratis
via de lokale Whisper-container).
