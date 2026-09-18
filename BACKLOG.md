# Backlog

Losse ideeën/wensen die (nog) niet ingepland zijn in een fase. Geen garantie op
volgorde — gewoon een geheugensteun voor later.

~~**Zoeken op tags**~~ — opgelost: de takenlijst heeft nu aanklikbare tag-checkboxes
waarmee je op meerdere tags tegelijk kunt filteren (OR-logica).

- **Achtergronden-systeem**: een instelling (waarschijnlijk bij Account → Weergave, naast
  thema/lettertype) om een achtergrondafbeelding voor de app te kiezen uit gratis
  online bronnen — categorieën natuur, omgeving en "in het donker". Aandachtspunt bij
  uitwerking: dit is de eerste plek in de app die bewust een externe, niet-self-hosted
  bron nodig heeft (bv. Unsplash/Pexels API of iets dat geen API-key vereist zoals Picsum),
  wat afwijkt van de rest van de app die verder geen externe data ophaalt buiten de
  webfonts. Moet afwegen: vaste per-categorie afbeeldingen bundelen (blijft self-hosted,
  minder keuze) vs. live ophalen bij een externe API (meer keuze, wel een netwerkcall en
  eventueel een API-key-vereiste voor de gebruiker).

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
