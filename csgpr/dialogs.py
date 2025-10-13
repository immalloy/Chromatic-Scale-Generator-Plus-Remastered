from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE


class CreditsDialog(QDialog):
    def __init__(self, lang: str, parent=None) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Credits"))
        self.setMinimumWidth(420)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)

        layout.addWidget(self._build_developers_section())

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _build_developers_section(self) -> QWidget:
        widget = QWidget(self)
        section_layout = QVBoxLayout(widget)

        text = QLabel(T(self.lang, "CreditsText"))
        text.setWordWrap(True)
        section_layout.addWidget(text)

        buttons_row = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang, "Join Discord"))
        self.discord_btn.setObjectName("LinkButton")
        self.discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DISCORD_INVITE))
        )
        buttons_row.addWidget(self.discord_btn)
        buttons_row.addStretch(1)
        section_layout.addLayout(buttons_row)
        section_layout.addStretch(1)
        return widget
