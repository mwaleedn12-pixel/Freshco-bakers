import re
import unicodedata

from sqlalchemy.orm import Session


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text or "item"


def unique_slug(db: Session, model, name: str) -> str:
    """Return a slug for `name` that is not yet used in `model.slug` (adds -2, -3... if needed)."""
    base = slugify(name)
    slug, counter = base, 2
    while db.query(model.id).filter(model.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug
