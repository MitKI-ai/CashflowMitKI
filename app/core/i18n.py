"""Internationalisation helper — STORY-034

Simple JSON-based translator. Supported locales: de, en.
Falls back to 'de' for unknown locales.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_TRANSLATIONS_DIR = Path(__file__).parent.parent.parent / "translations"
_SUPPORTED = {"de", "en"}
_DEFAULT = "de"


@lru_cache(maxsize=8)
def _load(locale: str) -> dict:
    path = _TRANSLATIONS_DIR / f"{locale}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not load translations/%s.json: %s", locale, exc)
        return {}


def get_translator(locale: str):
    """Return a t(key) callable for the given locale."""
    if locale not in _SUPPORTED:
        locale = _DEFAULT
    strings = _load(locale)

    def t(key: str) -> str:
        return strings.get(key, key)

    return t
