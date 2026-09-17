from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.services.colors import stable_hue


def generate_tag_color(name: str) -> str:
    """Geeft elke tagnaam een eigen, stabiele kleur (dezelfde naam -> altijd dezelfde
    kleur, ook na een herstart)."""
    return f"hsl({stable_hue(name)}, 65%, 50%)"


def resolve_tags(db: Session, raw: str) -> list[Tag]:
    """Parseert een komma-gescheiden tag-string en geeft bestaande/nieuwe Tag-objecten terug."""
    names = {name.strip() for name in raw.split(",") if name.strip()}
    if not names:
        return []

    existing = db.query(Tag).filter(Tag.name.in_(names)).all()
    existing_names = {tag.name for tag in existing}

    new_tags = [Tag(name=name, color=generate_tag_color(name)) for name in names if name not in existing_names]
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
        tag.color = generate_tag_color(tag.name)
    db.commit()
