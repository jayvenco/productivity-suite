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

**Voice-opname → taken/notities/etc. (Whisper + ChatGPT)**: een microfoonknop (bv. in het
quick-add-wiel) die een audiofragment opneemt, laat transcriberen via de OpenAI Whisper-API,
en de tekst vervolgens laat interpreteren door ChatGPT (structured output/JSON: welke actie —
taak/notitie/kanban-kaart/snippet — met welke velden). De uitvoering hergebruikt de bestaande
create-routes/services (dezelfde die de agent-API al gebruikt), dus geen herbouw van de
kernlogica nodig — vooral een nieuwe route (`POST /voice/command`) + opname-UI + een
bevestigingsstapje ("Ik heb begrepen: taak 'X' aanmaken — klopt dat?") vóór het echt opslaat,
want STT + AI-interpretatie gaat af en toe mis. Kosten: verwaarloosbaar voor persoonlijk
gebruik (Whisper ~€0,006/min + een kleine ChatGPT-prompt per commando). Alternatief voor
Whisper-API: lokaal `faster-whisper` op de Unraid-server (gratis, geen API-kosten, wel meer
CPU/RAM-gebruik en een extra dependency in de Docker-image) — kan later als upgrade als
volledig gratis/offline gewenst is.
