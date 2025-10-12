# i18n_pkg/lang_core.py
from __future__ import annotations
from typing import Dict

from .meta import APP_VERSION, RELEASE_MONTH, RELEASE_YEAR, get_month_name

# Import language dictionaries (each in its own file)
from .lang_en import STRINGS as en
from .lang_es import STRINGS as es
from .lang_pt_br import STRINGS as pt_br
from .lang_hi import STRINGS as hi
from .lang_zh import STRINGS as zh
from .lang_bn import STRINGS as bn
from .lang_ru import STRINGS as ru
from .lang_ja import STRINGS as ja
from .lang_fr import STRINGS as fr
from .lang_ko import STRINGS as ko
from .lang_id import STRINGS as id

# Register languages here
LANGS: Dict[str, Dict[str, str]] = {
    "en": en,
    "es": es,
    "pt_br": pt_br,
    "hi": hi,
    "zh": zh,
    "bn": bn,
    "ru": ru,
    "ja": ja,
    "fr": fr,
    "ko": ko,
    "id": id,
}

# Human-friendly names for dropdowns
NAMES: Dict[str, str] = {
    "en": "English",
    "es": "Español",
    "pt_br": "Português (Brasil)",
    "hi": "हिन्दी (Hindi)",
    "zh": "中文 (Chinese)",
    "bn": "বাংলা (Bengali)",
    "ru": "Русский (Russian)",
    "ja": "日本語 (Japanese)",
    "fr": "Français (French)",
    "ko": "한국어 (Korean)",
    "id": "Indonesia (Indonesian)"
}

def list_languages():
    """Return list of (code, display_name) tuples for the UI."""
    return [(code, NAMES.get(code, code)) for code in LANGS.keys()]

def get_lang(code: str) -> Dict[str, str]:
    return LANGS.get(code, en)

def _base_context(lang: str) -> Dict[str, str]:
    return {
        "version": APP_VERSION,
        "year": str(RELEASE_YEAR),
        "month_number": str(RELEASE_MONTH),
        "month_name": get_month_name(lang),
    }


def T(lang: str, key: str, **kwargs) -> str:
    # Fallback to English if missing
    table = get_lang(lang)
    s = table.get(key, en.get(key, key))
    try:
        ctx = _base_context(lang)
        ctx.update(kwargs)
        return s.format(**ctx)
    except Exception:
        return s
