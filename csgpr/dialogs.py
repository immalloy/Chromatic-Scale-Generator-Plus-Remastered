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

from i18n_pkg import T, list_languages

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
    """Modal dialog that allows the user to configure UI preferences."""

    def __init__(
        self,
        lang: str,
        mode: str,
        accent: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(420)

        self.preview_lang = lang
        self.preview_mode = mode
        self.preview_accent = accent

        self.theme_options = ["dark", "light"]
        self.accent_options = ["blue", "pink"]

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        self.description = QLabel()
        self.description.setWordWrap(True)
        layout.addWidget(self.description)

        form = QFormLayout()
        form.setSpacing(12)

        self.theme_label = QLabel()
        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(self._update_theme)
        form.addRow(self.theme_label, self.theme_combo)

        self.accent_label = QLabel()
        self.accent_combo = QComboBox()
        self.accent_combo.currentIndexChanged.connect(self._update_accent)
        form.addRow(self.accent_label, self.accent_combo)

        self.language_label = QLabel()
        self.lang_combo = QComboBox()
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        form.addRow(self.language_label, self.lang_combo)

        layout.addLayout(form)

        self.button_box = QDialogButtonBox()
        self.apply_button = self.button_box.addButton(
            "Apply", QDialogButtonBox.AcceptRole
        )
        self.cancel_button = self.button_box.addButton(
            QDialogButtonBox.Cancel
        )
        self.apply_button.clicked.connect(self._accept)
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.button_box)

        self.retranslate()

    def retranslate(self) -> None:
        lang = self.preview_lang
        self.setWindowTitle(T(lang, "Settings"))
        self.description.setText(
            T(lang, "Adjust appearance and language preferences.")
        )
        self.theme_label.setText(T(lang, "Theme:"))
        self.accent_label.setText(T(lang, "Accent:"))
        self.language_label.setText(T(lang, "Language:"))

        self._populate_combo(self.theme_combo, self.theme_options, self.preview_mode)
        self._populate_combo(self.accent_combo, self.accent_options, self.preview_accent)
        self._populate_languages()

        self.apply_button.setText(T(lang, "Apply"))
        self.cancel_button.setText(T(lang, "Cancel"))

    def _populate_combo(self, combo: QComboBox, items: list[str], current: str) -> None:
        lang = self.preview_lang
        combo.blockSignals(True)
        combo.clear()
        for value in items:
            if value == "dark":
                label = T(lang, "Dark")
            elif value == "light":
                label = T(lang, "Light")
            elif value == "blue":
                label = T(lang, "Blue")
            elif value == "pink":
                label = T(lang, "Pink")
            else:
                label = value
            combo.addItem(label, value)
        idx = combo.findData(current)
        if idx < 0:
            idx = 0
        combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _populate_languages(self) -> None:
        combo = self.lang_combo
        combo.blockSignals(True)
        combo.clear()
        for code, label in list_languages():
            combo.addItem(label, code)
        idx = combo.findData(self.preview_lang)
        if idx < 0:
            idx = 0
        combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _update_theme(self) -> None:
        data = self.theme_combo.currentData()
        if data:
            self.preview_mode = str(data)

    def _update_accent(self) -> None:
        data = self.accent_combo.currentData()
        if data:
            self.preview_accent = str(data)

    def _on_language_changed(self) -> None:
        data = self.lang_combo.currentData()
        if data:
            self.preview_lang = str(data)
            self.retranslate()

    def _accept(self) -> None:
        self._update_theme()
        self._update_accent()
        data = self.lang_combo.currentData()
        if data:
            self.preview_lang = str(data)
        self.accept()

    def values(self) -> tuple[str, str, str]:
        return self.preview_mode, self.preview_accent, self.preview_lang
