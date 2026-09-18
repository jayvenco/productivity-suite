# Backlog

Losse ideeën/wensen die (nog) niet ingepland zijn in een fase. Geen garantie op
volgorde — gewoon een geheugensteun voor later.

~~**Zoeken op tags**~~ — opgelost: de takenlijst heeft nu aanklikbare tag-checkboxes
waarmee je op meerdere tags tegelijk kunt filteren (OR-logica).

~~**Achtergronden-systeem**~~ — opgelost: Account → Weergave heeft nu een achtergrondkeuze
(Geen/Natuur/Bergen/Heelal) met een sterkte-schuifje. Gekozen voor drie vaste, self-hosted
foto's i.p.v. een live externe API — geen netwerkafhankelijkheid, in lijn met de rest van de
app. Meer categorieën/foto's toevoegen kan later alsnog als daar behoefte aan is.

- **API voor externe agents/automatisering** (taken, snippets, kanban-kaarten, notities
  aanmaken vanaf buiten de app, bv. vanuit een eigen agent-script): gematigd complex, geen
  herontwerp nodig, maar wel een aparte laag naast de bestaande routes. De huidige routes
  zijn form-based en geven HTML-redirects terug, geen JSON, dus dit wordt een nieuwe
  `/api/v1/...`-laag die dezelfde services (`resolve_tags`, model-CRUD) hergebruikt maar JSON
  in/uit levert. Voor authenticatie is een los API-token nodig (bv. gegenereerd op de
  Account-pagina, gecontroleerd via een nieuwe auth-dependency die zowel de sessie-cookie als
  een `Authorization: Bearer <token>`-header accepteert) — de huidige sessie-cookie-auth is
  namelijk niet praktisch voor een extern script. Uitdrukkelijk als laatste op de lijst
  gezet.
