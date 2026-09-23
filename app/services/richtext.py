from __future__ import annotations

import bleach

# Alleen de tags/attributen die de notitie-editor zelf kan produceren (zie
# app/static/js/notes.js). We renderen opgeslagen notitie-HTML met |safe, dus
# alles wat hier niet in staat (script, event handlers, iframes, ...) wordt
# eruit gefilterd -- ook nuttig als iemand iets van buitenaf in de editor plakt.
ALLOWED_TAGS = [
    "p", "br", "div",
    "b", "strong", "i", "em", "u",
    "h2", "h3",
    "ul", "ol", "li",
    "a", "code", "pre", "blockquote",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "rel", "target"]}


def sanitize_note_html(raw_html: str) -> str:
    """Ruimt de HTML uit de notitie-editor op en maakt daarna kale URL's (getypt
    of geplakt, met of zonder www./schema, nog niet in een <a>-tag) alsnog
    automatisch aanklikbaar -- naast de bestaande "Link"-werkbalkknop, die een
    expliciete link met eigen linktekst invoegt."""
    cleaned = bleach.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return bleach.linkify(cleaned, parse_email=False)
