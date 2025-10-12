from __future__ import annotations

"""Shared constants for the Chromatic Scale Generator PLUS!"""

from pathlib import Path
import sys

from PySide6.QtCore import QSize


def _base_dir() -> Path:
    """Return the directory where bundled resources live.

    When frozen via PyInstaller the resources are extracted to ``_MEIPASS``.
    Otherwise we fall back to the project root (two levels above this file).
    """

    root = getattr(sys, "_MEIPASS", None)  # type: ignore[attr-defined]
    if root:
        return Path(root)
    return Path(__file__).resolve().parent.parent


APP_TITLE = "Chromatic Scale Generator Plus Remastered"
APP_ICON_PATH = str(_base_dir() / "icon.ico")
DEFAULT_SR = 48000
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
OCTAVES = list(range(1, 9))
MAX_SEMITONES = 128
MAX_GAP_SEC = 5.0
DISCORD_INVITE = "https://discord.gg/pe6J4FbcCU"
PROJECT_WIKI_URL = (
    "https://github.com/immalloy/Chromatic-Scale-Generator-Plus-Remastered/wiki"
)
PROJECT_TUTORIAL_URL = (
    "https://github.com/immalloy/Chromatic-Scale-Generator-Plus-Remastered/wiki/Tutorial"
)
SPLASH_SIZE = QSize(1280, 720)
SPLASH_ART_PATH = str(_base_dir() / "assets" / "sirthegamercodersplash.png")
SPLASH_CONFIG_PATH = str(_base_dir() / "assets" / "splashes.json")
SPLASH_MIN_DURATION_MS = 2500
