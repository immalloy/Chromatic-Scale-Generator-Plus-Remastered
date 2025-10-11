from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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
        self.setAttribute(Qt.WA_StyledBackground, True)

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


class SettingsDialog(QDialog):
    def __init__(
        self,
        lang: str,
        mode: str,
        accent: str,
        languages: list[tuple[str, str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Settings"))
        self.setMinimumWidth(360)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["dark", "light"])
        if mode in {"dark", "light"}:
            self.mode_combo.setCurrentText(mode)

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["blue", "pink"])
        if accent in {"blue", "pink"}:
            self.accent_combo.setCurrentText(accent)

        self.lang_combo = QComboBox()
        for code, label in languages:
            self.lang_combo.addItem(label, code)
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        form.addRow(T(self.lang, "Theme:"), self.mode_combo)
        form.addRow(T(self.lang, "Accent:"), self.accent_combo)
        form.addRow(T(self.lang, "Language:"), self.lang_combo)

        layout.addLayout(form)
        layout.addStretch(1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def selected_values(self) -> tuple[str, str, str]:
        lang_code = self.lang_combo.currentData()
        if not lang_code:
            lang_code = self.lang
        return (
            self.mode_combo.currentText(),
            self.accent_combo.currentText(),
            str(lang_code),
        )
