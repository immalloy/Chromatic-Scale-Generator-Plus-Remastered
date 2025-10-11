from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE


@dataclass
class SettingsState:
    """Mutable snapshot of user settings toggles."""

    language: str
    auto_reload: bool
    output_path: str
    verbose_logging: bool
    reset_layout: bool = False


class CreditsDialog(QDialog):
    """Credits modal with a simple call-to-action."""

    def __init__(self, lang: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Credits"))
        self.setMinimumWidth(440)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        text = QLabel(T(self.lang, "CreditsText"))
        text.setWordWrap(True)
        layout.addWidget(text)

        buttons_row = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang, "Join Discord"))
        self.discord_btn.setObjectName("QuickActionLink")
        self.discord_btn.clicked.connect(self._open_discord)
        buttons_row.addWidget(self.discord_btn)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _open_discord(self) -> None:
        from PySide6.QtGui import QDesktopServices, QCursor
        from PySide6.QtCore import QUrl

        QDesktopServices.openUrl(QUrl(DISCORD_INVITE))
        self.setCursor(QCursor(Qt.ArrowCursor))


class SettingsDialog(QDialog):
    """Dialog presenting the remaining runtime preferences."""

    def __init__(
        self,
        *,
        lang: str,
        languages: Sequence[tuple[str, str]],
        state: SettingsState,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.lang = lang
        self._languages = list(languages)
        self._initial_state = state

        self.setWindowTitle(T(self.lang, "Settings"))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(520, 420)

        outer = QVBoxLayout(self)
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        self.lang_combo = QComboBox()
        for code, label in self._languages:
            self.lang_combo.addItem(label, code)
        index = self.lang_combo.findData(state.language)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)

        self.auto_reload_box = QCheckBox(
            T(self.lang, "AutoReloadTranslations")
        )
        self.auto_reload_box.setChecked(state.auto_reload)

        lang_tab = QWidget()
        lang_layout = QVBoxLayout(lang_tab)
        lang_layout.setSpacing(16)
        lang_layout.setContentsMargins(16, 16, 16, 16)
        lang_form = QFormLayout()
        lang_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        lang_form.addRow(T(self.lang, "LanguageLabel"), self.lang_combo)
        lang_layout.addLayout(lang_form)
        lang_layout.addWidget(self.auto_reload_box)
        lang_layout.addStretch(1)
        self.tabs.addTab(lang_tab, T(self.lang, "SettingsTabLanguage"))

        self.output_edit = QLineEdit(state.output_path)
        self.output_edit.setPlaceholderText(T(self.lang, "OutputFolderPlaceholder"))
        self.output_edit.setClearButtonEnabled(True)
        self.output_edit.setObjectName("PathEntry")
        browse_btn = QPushButton(T(self.lang, "Browse…"))
        browse_btn.setObjectName("PrimaryAction")
        browse_btn.clicked.connect(self._choose_output)

        path_tab = QWidget()
        path_layout = QVBoxLayout(path_tab)
        path_layout.setSpacing(16)
        path_layout.setContentsMargins(16, 16, 16, 16)
        path_form = QFormLayout()
        path_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        row = QHBoxLayout()
        row.addWidget(self.output_edit, 1)
        row.addWidget(browse_btn, 0)
        path_form.addRow(T(self.lang, "OutputFolder"), row)
        path_layout.addLayout(path_form)
        path_layout.addStretch(1)
        self.tabs.addTab(path_tab, T(self.lang, "SettingsTabPaths"))

        self.verbose_box = QCheckBox(T(self.lang, "EnableVerboseLogging"))
        self.verbose_box.setChecked(state.verbose_logging)
        self.reset_box = QCheckBox(T(self.lang, "ResetWindowLayout"))

        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setSpacing(16)
        advanced_layout.setContentsMargins(16, 16, 16, 16)
        advanced_layout.addWidget(self.verbose_box)
        advanced_layout.addWidget(self.reset_box)
        advanced_layout.addStretch(1)
        self.tabs.addTab(advanced_tab, T(self.lang, "SettingsTabAdvanced"))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _choose_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            T(self.lang, "Select Output Folder"),
            str(Path(self.output_edit.text() or Path.home())),
        )
        if directory:
            self.output_edit.setText(directory)

    def selected_values(self) -> SettingsState:
        lang_code = self.lang_combo.currentData() or self._initial_state.language
        return SettingsState(
            language=str(lang_code),
            auto_reload=self.auto_reload_box.isChecked(),
            output_path=self.output_edit.text().strip(),
            verbose_logging=self.verbose_box.isChecked(),
            reset_layout=self.reset_box.isChecked(),
        )
