# i18n_pkg/__init__.py
from .lang_core import LANGS, list_languages, get_lang, T
from .meta import APP_VERSION, RELEASE_MONTH, RELEASE_YEAR, get_month_name

__all__ = [
    "LANGS",
    "list_languages",
    "get_lang",
    "T",
    "APP_VERSION",
    "RELEASE_MONTH",
    "RELEASE_YEAR",
    "get_month_name",
]
