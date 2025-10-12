from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

import json
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE, SPLASH_CONFIG_PATH


class CreditsDialog(QDialog):
    def __init__(self, lang: str, parent=None) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Credits"))
        self.setMinimumWidth(420)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)

        tabs = QTabWidget(self)
        tabs.addTab(self._build_developers_tab(), T(self.lang, "CreditsTabDevelopers"))
        tabs.addTab(
            self._build_splash_artists_tab(),
            T(self.lang, "CreditsTabSplashArtists"),
        )
        layout.addWidget(tabs)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _build_developers_tab(self) -> QWidget:
        widget = QWidget(self)
        tab_layout = QVBoxLayout(widget)

        text = QLabel(T(self.lang, "CreditsText"))
        text.setWordWrap(True)
        tab_layout.addWidget(text)

        buttons_row = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang, "Join Discord"))
        self.discord_btn.setObjectName("LinkButton")
        self.discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DISCORD_INVITE))
        )
        buttons_row.addWidget(self.discord_btn)
        buttons_row.addStretch(1)
        tab_layout.addLayout(buttons_row)
        tab_layout.addStretch(1)
        return widget

    def _build_splash_artists_tab(self) -> QWidget:
        widget = QWidget(self)
        tab_layout = QVBoxLayout(widget)

        description = QLabel(T(self.lang, "CreditsSplashDescription"))
        description.setWordWrap(True)
        tab_layout.addWidget(description)

        artists = _load_splash_artist_names()
        if artists:
            list_widget = QListWidget()
            list_widget.setObjectName("CreditsSplashArtistList")
            list_widget.setSelectionMode(QListWidget.NoSelection)
            list_widget.setFocusPolicy(Qt.NoFocus)
            list_widget.setAlternatingRowColors(True)
            for name in artists:
                list_widget.addItem(name)
            tab_layout.addWidget(list_widget)
        else:
            empty_label = QLabel(T(self.lang, "CreditsSplashNone"))
            empty_label.setWordWrap(True)
            tab_layout.addWidget(empty_label)

        tab_layout.addStretch(1)
        return widget


def _load_splash_artist_names() -> list[str]:
    """Return a sorted list of splash artist names from configuration."""

    config_path = Path(SPLASH_CONFIG_PATH)
    if not config_path.exists():
        return []

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    entries = data.get("splashes")
    if not isinstance(entries, list):
        return []

    names: dict[str, None] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_names = entry.get("artists")
        if isinstance(raw_names, str):
            raw_names = [raw_names]
        if isinstance(raw_names, list):
            for candidate in raw_names:
                if isinstance(candidate, str):
                    name = candidate.strip()
                    if name and name not in names:
                        names[name] = None

    return sorted(names.keys(), key=str.casefold)
