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
