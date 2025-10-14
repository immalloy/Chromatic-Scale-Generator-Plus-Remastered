"""Shared metadata for Chromatic Scale Generator PLUS translations."""
from __future__ import annotations

from typing import Dict, List

APP_VERSION: str = "4.0.0-beta"
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
    "id": [
        "",
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]
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


# English baseline strings reused across language tables. Individual translation
# modules can copy these defaults and override only the entries that differ.
BASE_STRINGS: Dict[str, str] = {
    "Configuration": "Configuration",
    "Sample folder": "Sample folder",
    "Select a folder containing 1.wav, 2.wav, ...": "Select a folder containing 1.wav, 2.wav, ...",
    "Browse…": "Browse…",
    "Starting note": "Starting note",
    "Starting octave": "Starting octave",
    "Semitone range": "Semitone range",
    "Gap (seconds)": "Gap (seconds)",
    "Apply pitch transformation": "Apply pitch transformation",
    "Dump individual pitched samples": "Dump individual pitched samples",
    "Randomize sample selection": "Randomize sample selection",
    "Peak normalize each sample (pre-pitch)": "Peak normalize each sample (pre-pitch)",
    "Embed FL Studio Slicex slice markers": "Embed FL Studio Slicex slice markers",
    "Theme:": "Theme:",
    "Accent:": "Accent:",
    "Language:": "Language:",
    "Run": "Run",
    "Generate Chromatic": "Generate Chromatic",
    "Cancel": "Cancel",
    "Open Output Folder": "Open Output Folder",
    "Logs will appear here…": "Logs will appear here…",
    "Credits": "Credits",
    "Wiki": "Wiki",
    "Tutorial": "Tutorial",
    "&Help": "&Help",
    "Folder not found.": "Folder not found.",
    "Need at least 1.wav in this folder.": "Need at least 1.wav in this folder.",
    "No sequential samples found (1.wav, 2.wav, ...).": "No sequential samples found (1.wav, 2.wav, ...).",
    "Select Sample Folder": "Select Sample Folder",
    "Selected folder: {p}": "Selected folder: {p}",
    "No output file yet.": "No output file yet.",
    "Invalid folder. Place '1.wav', '2.wav', ... in it.": "Invalid folder. Place '1.wav', '2.wav', ... in it.",
    "'{name}' already exists. Overwrite?": "'{name}' already exists. Overwrite?",
    "Cancelled by user.": "Cancelled by user.",
    "Generating…": "Generating…",
    "Cancelling…": "Cancelling…",
    "Done! Saved to {p}": "Done! Saved to {p}",
    "An error occurred.": "An error occurred.",
    "⚠️ Generation was cancelled.": "⚠️ Generation was cancelled.",
    "Footer": "Original tool by @ChillSpaceIRL • Remastered by @nullfreq_ and Malloy | Version {version} • {month_name} {year}",
    "Join Discord": "Join Discord",
    "CreditsText": "Chromatic Scale Generator Plus Remastered\n\nOriginal tool by @ChillSpaceIRL\nRemastered by @nullfreq_ and Malloy\nVersion {version} • {month_name} {year}\n\nThanks for using the app!",
    "CreditsTabAbout": "About",
    "CreditsTabContributors": "Contributors",
    "CreditsContributorsLoading": "Loading contributors…",
    "CreditsContributorsNone": "No contributors found.",
    "CreditsContributorsError": "Couldn't load contributors.",
    "Found {n} sample(s) (1.wav..{m}.wav).": "Found {n} sample(s) (1.wav..{m}.wav).",
    "Semitones: {s} | Gap: {g:.3f}s | Pitched: {p}": "Semitones: {s} | Gap: {g:.3f}s | Pitched: {p}",
    "Peak normalization: ON": "Peak normalization: ON",
    "[{a}/{b}] Loading {name}": "[{a}/{b}] Loading {name}",
    "normalized": "normalized",
    "Concatenating chromatic scale...": "Concatenating chromatic scale...",
    "Embedding FL Studio Slicex slice markers...": "Embedding FL Studio Slicex slice markers...",
    "Saved: {path}": "Saved: {path}",
    "Dumped {n} pitched sample(s) to: {dir}": "Dumped {n} pitched sample(s) to: {dir}",
}

