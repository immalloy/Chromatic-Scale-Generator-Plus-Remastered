# i18n_pkg/lang_core.py
from __future__ import annotations
from typing import Dict, Callable

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
}

def list_languages():
    """Return list of (code, display_name) tuples for the UI."""
    return [(code, NAMES.get(code, code)) for code in LANGS.keys()]

def get_lang(code: str) -> Dict[str, str]:
    return LANGS.get(code, en)

def T(lang: str, key: str, **kwargs) -> str:
    # Fallback to English if missing
    table = get_lang(lang)
    s = table.get(key, en.get(key, key))
    try:
        return s.format(**kwargs)
    except Exception:
        return s
