"""Text helpers for accent-insensitive search."""

import unicodedata


def normalize_text(*parts: str | None) -> str:
    """Normalize text for accent-insensitive matching.

    Joins the given parts, lowercases them, and strips diacritics so that
    ``"Câmera"`` and ``"camera"`` compare equal.

    Args:
        *parts (str | None): Text fragments to combine; ``None`` values are ignored.

    Returns:
        str: A lowercased, accent-free, single-spaced string.
    """
    joined = " ".join(part for part in parts if part)
    decomposed = unicodedata.normalize("NFKD", joined)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(without_marks.lower().split())
