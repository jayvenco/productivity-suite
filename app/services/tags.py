from __future__ import annotations

import random

from sqlalchemy.orm import Session

from app.models.tag import Tag


def generate_tag_color() -> str:
    """Geeft een nieuwe tag een eigen, willekeurige kleur. Wordt eenmalig bij aanmaak
    bepaald en opgeslagen op de Tag, dus blijft daarna stabiel voor die tag."""
    return f"hsl({random.randint(0, 359)}, 65%, 50%)"


def first_tag_hue_style(tags: list[Tag]) -> str:
    """Zet de tint van de eerste tag als CSS custom property (--tag-hue) i.p.v. een
    kant-en-klare kleur -- gebruikt door Task/Note/Snippet.row_tint_style, zodat elk
    thema zelf kan bepalen hoe (of óf) die tint toegepast wordt op de kaart (zie
    .snippet-card[style*="--tag-hue"] in app.css voor de standaard lichte tint, en
    themes/bubbles.css voor een thema met een volle kleur i.p.v. een lichte tint).
    Geeft een lege string als er geen tags zijn of de eerste tag geen geldige hue heeft
    (bv. een oude/handmatige hex-kleur)."""
    if not tags:
        return ""
    hue = tags[0].hue
    if hue is None:
        return ""
    return f"--tag-hue: {hue};"


def resolve_tags(db: Session, raw: str) -> list[Tag]:
    """Parseert een komma-gescheiden tag-string en geeft bestaande/nieuwe Tag-objecten terug."""
    names = {name.strip() for name in raw.split(",") if name.strip()}
    if not names:
        return []

    existing = db.query(Tag).filter(Tag.name.in_(names)).all()
    existing_names = {tag.name for tag in existing}

    new_tags = [Tag(name=name, color=generate_tag_color()) for name in names if name not in existing_names]
    db.add_all(new_tags)
    if new_tags:
        db.flush()

    return existing + new_tags


_OLD_DEFAULT_COLOR = "#6c7086"


def backfill_tag_colors(db: Session) -> None:
    """Eenmalige opschoning voor tags die zijn aangemaakt vóórdat elke tag een eigen
    kleur kreeg -- geeft ze alsnog een stabiele, onderscheidende kleur."""
    stale_tags = db.query(Tag).filter(Tag.color == _OLD_DEFAULT_COLOR).all()
    if not stale_tags:
        return
    for tag in stale_tags:
        tag.color = generate_tag_color()
    db.commit()
