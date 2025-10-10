"""Shared metadata for Chromatic Scale Generator PLUS translations."""
from __future__ import annotations

from typing import Dict, List

APP_VERSION: str = "3.1.3"
RELEASE_YEAR: int = 2025 #cmon how did i forget THIS
RELEASE_MONTH: int = 10  # October, I forgot shit

_MONTH_NAMES: Dict[str, List[str]] = {
    "en": [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
    "es": [
        "",
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ],
    "pt_br": [
        "",
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ],
    "hi": [
        "",
        "जनवरी",
        "फ़रवरी",
        "मार्च",
        "अप्रैल",
        "मई",
        "जून",
        "जुलाई",
        "अगस्त",
        "सितंबर",
        "अक्टूबर",
        "नवंबर",
        "दिसंबर",
    ],
    "bn": [
        "",
        "জানুয়ারি",
        "ফেব্রুয়ারি",
        "মার্চ",
        "এপ্রিল",
        "মে",
        "জুন",
        "জুলাই",
        "আগস্ট",
        "সেপ্টেম্বর",
        "অক্টোবর",
        "নভেম্বর",
        "ডিসেম্বর",
    ],
    "ru": [
        "",
        "Январь",
        "Февраль",
        "Март",
        "Апрель",
        "Май",
        "Июнь",
        "Июль",
        "Август",
        "Сентябрь",
        "Октябрь",
        "Ноябрь",
        "Декабрь",
    ],
    "fr": [
        "",
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ],
}


def get_month_name(lang: str) -> str:
    """Return the localized month name for the configured release month."""
    if RELEASE_MONTH < 1 or RELEASE_MONTH > 12:
        raise ValueError("RELEASE_MONTH must be between 1 and 12")

    if lang in {"zh"}:
        return f"{RELEASE_MONTH}月"
    if lang in {"ja"}:
        return f"{RELEASE_MONTH}月"
    if lang in {"ko"}:
        return f"{RELEASE_MONTH}월"

    names = _MONTH_NAMES.get(lang, _MONTH_NAMES["en"])
    return names[RELEASE_MONTH]

