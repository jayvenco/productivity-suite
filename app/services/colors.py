from __future__ import annotations

import hashlib


def stable_hue(name: str) -> int:
    """Geeft een stabiele HSL-tint (0-359) voor een naam terug -- dezelfde naam geeft
    altijd dezelfde tint, ook na een herstart. Gebaseerd op een hash i.p.v. Python's
    ingebouwde hash() omdat die per proces varieert (hash-randomisatie)."""
    digest = hashlib.md5(name.strip().lower().encode()).hexdigest()
    return int(digest[:8], 16) % 360
