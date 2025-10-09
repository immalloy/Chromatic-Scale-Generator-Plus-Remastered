from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE


class CreditsDialog(QDialog):
    def __init__(self, lang: str, parent=None) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Credits"))
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        text = QLabel(T(self.lang, "CreditsText"))
        text.setWordWrap(True)
        layout.addWidget(text)

        buttons_row = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang, "Join Discord"))
        self.discord_btn.setObjectName("LinkButton")
        self.discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DISCORD_INVITE))
        )
        buttons_row.addWidget(self.discord_btn)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
