from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tag import Tag


def resolve_tags(db: Session, raw: str) -> list[Tag]:
    """Parseert een komma-gescheiden tag-string en geeft bestaande/nieuwe Tag-objecten terug."""
    names = {name.strip() for name in raw.split(",") if name.strip()}
    if not names:
        return []

    existing = db.query(Tag).filter(Tag.name.in_(names)).all()
    existing_names = {tag.name for tag in existing}

    new_tags = [Tag(name=name) for name in names if name not in existing_names]
    db.add_all(new_tags)
    if new_tags:
        db.flush()

    return existing + new_tags
