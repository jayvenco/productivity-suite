from __future__ import annotations

import html as _html
import re

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
    "img", "s", "del", "hr",
]
# ul[class] + li[data-checked]: afvinkbare checklists van de rich-text-editor (static/js/rich-editor.js)
ALLOWED_ATTRIBUTES = {
    "a": ["href", "rel", "target"],
    "img": ["src", "alt"],
    "ul": ["class"],
    "li": ["data-checked"],
}
# Geplakte afbeeldingen worden als data-URI opgeslagen (img src="data:..."), dus
# bleach moet naast http/https/mailto ook het "data"-schema toestaan.
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "data"]


def sanitize_note_html(raw_html: str) -> str:
    """Ruimt de HTML uit de notitie-editor op en maakt daarna kale URL's (getypt
    of geplakt, met of zonder www./schema, nog niet in een <a>-tag) alsnog
    automatisch aanklikbaar -- naast de bestaande "Link"-werkbalkknop, die een
    expliciete link met eigen linktekst invoegt."""
    cleaned = bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned, parse_email=False)


# ---- Rich text voor taken, kanban-kaarten en de inbox ----
# Deze velden bevatten voortaan HTML van de rich-text-editor; bestaande rijen met platte tekst of
# markdown blijven werken (zie looks_like_html / de filters in app/templating.py).

_HTML_HINT = re.compile(r"<(p|div|br|ul|ol|li|h[1-6]|blockquote|pre|strong|b|em|i|u|s|a|img|hr)\b", re.I)
_CHECK_LI = re.compile(r'<li\b[^>]*\bdata-checked="([01])"[^>]*>', re.I)
_FIRST_BLOCK = re.compile(r"</(p|div|h[1-6]|li|blockquote|pre)>", re.I)


def looks_like_html(text: str | None) -> bool:
    return bool(text and _HTML_HINT.search(text))


def sanitize_rich(text: str | None) -> str:
    """HTML van de editor opschonen; platte tekst (bv. via de API) blijft ongemoeid."""
    if not text:
        return ""
    return sanitize_note_html(text) if looks_like_html(text) else text


def plain_text(text: str | None) -> str:
    """Tekst zonder opmaak, voor korte previews (bv. de beschrijving op een taakkaart)."""
    if not text:
        return ""
    if not looks_like_html(text):
        return text
    spaced = re.sub(r"</(p|div|h[1-6]|li|blockquote|pre)>|<br\s*/?>", " ", text, flags=re.I)
    stripped = bleach.clean(spaced, tags=[], strip=True)
    return re.sub(r"\s+", " ", _html.unescape(stripped)).strip()


def split_rich(text: str) -> tuple[str, str]:
    """Eerste regel/blok = titel (platte tekst, max. 200), de rest blijft (HTML-)tekst."""
    text = (text or "").strip()
    if not looks_like_html(text):
        lines = text.splitlines()
        title = ""
        rest_start = len(lines)
        for index, line in enumerate(lines):
            if line.strip():
                title = line.strip()[:200]
                rest_start = index + 1
                break
        return title, "\n".join(lines[rest_start:]).strip()

    # Kale eerste regel gevolgd door een blok ("titel<div>rest</div>"): de browser maakt zo'n
    # structuur als er geen alinea-element omheen staat.
    lead = re.match(r"^([^<]+?)\s*(?=<(?:div|p|ul|ol|h[1-6]|blockquote|pre|br)\b)", text, re.I)
    if lead and lead.group(1).strip():
        return _html.unescape(lead.group(1).strip())[:200], text[lead.end():].strip()

    match = _FIRST_BLOCK.search(text)
    first, rest = (text[: match.end()], text[match.end():]) if match else (text, "")
    first_line = re.split(r"<br\s*/?>", first, maxsplit=1, flags=re.I)
    title = plain_text(first_line[0])[:200]
    if len(first_line) > 1:  # "titel<br>rest" binnen één blok: de rest hoort bij de beschrijving
        rest = f"<p>{first_line[1]}" + rest
    return title, rest.strip()


def html_checklist_progress(text: str | None) -> tuple[int, int]:
    """(afgevinkt, totaal) van de afvinkbare items in HTML-inhoud."""
    marks = _CHECK_LI.findall(text or "")
    return sum(1 for m in marks if m == "1"), len(marks)


def toggle_html_checklist(text: str, index: int) -> str:
    """Wisselt data-checked van het index-de afvinkbare item (0-based) om."""
    count = -1

    def flip(match: re.Match) -> str:
        nonlocal count
        count += 1
        if count != index:
            return match.group(0)
        new = "0" if match.group(1) == "1" else "1"
        return match.group(0).replace(f'data-checked="{match.group(1)}"', f'data-checked="{new}"', 1)

    return _CHECK_LI.sub(flip, text)
