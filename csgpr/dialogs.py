from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

from typing import Iterable, List, Sequence

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE
from .custom_order import (
    CustomOrderPreset,
    PreviewItem,
    SelectionPolicy,
)


__all__ = ["CreditsDialog", "PresetEditorDialog", "CustomPreviewDialog"]


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


class PresetEditorDialog(QDialog):
    def __init__(
        self,
        lang: str,
        allowed_symbols: Iterable[str],
        *,
        preset: CustomOrderPreset | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.lang = lang
        self.allowed_symbols: List[str] = [s.upper() for s in allowed_symbols]
        self._result: CustomOrderPreset | None = None

        self.setWindowTitle(T(self.lang, "Edit Preset"))
        self.setMinimumWidth(460)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name_edit = QLineEdit()
        form.addRow(T(self.lang, "Preset Name"), self.name_edit)

        self.order_edit = QLineEdit()
        self.order_edit.setPlaceholderText(
            T(self.lang, "Enter symbols separated by spaces (A E I O U AY)")
        )
        form.addRow(T(self.lang, "Order"), self.order_edit)

        self.policy_combo = self._build_combo(
            [
                (T(self.lang, "SelectionFirst"), "first"),
                (T(self.lang, "SelectionCycle"), "cycle"),
                (T(self.lang, "SelectionRandom"), "random"),
            ]
        )
        form.addRow(T(self.lang, "Selection policy"), self.policy_combo)

        self.seed_spin = QSpinBox()
        self.seed_spin.setRange(0, 999999)
        self.seed_spin.setEnabled(False)
        form.addRow(T(self.lang, "Seed"), self.seed_spin)

        self.length_combo = self._build_combo(
            [
                (T(self.lang, "LengthPad"), "pad"),
                (T(self.lang, "LengthTruncate"), "truncate"),
                (T(self.lang, "LengthError"), "error"),
            ]
        )
        form.addRow(T(self.lang, "Length handling"), self.length_combo)

        self.missing_combo = self._build_combo(
            [
                (T(self.lang, "MissingSkip"), "skip"),
                (T(self.lang, "MissingAsk"), "ask"),
                (T(self.lang, "MissingError"), "error"),
            ]
        )
        form.addRow(T(self.lang, "Missing symbol"), self.missing_combo)

        layout.addWidget(QLabel(T(self.lang, "Order Preview")))
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.policy_combo.currentIndexChanged.connect(self._on_policy_changed)
        self.order_edit.textChanged.connect(self.refresh_preview)

        if preset:
            self._load_preset(preset)
        else:
            self.policy_combo.setCurrentIndex(0)
            self.length_combo.setCurrentIndex(0)
            self.missing_combo.setCurrentIndex(0)

        self.refresh_preview()

    def _build_combo(self, items: Iterable[tuple[str, str]]) -> QComboBox:
        combo = QComboBox()
        for label, value in items:
            combo.addItem(label, value)
        return combo

    def _on_policy_changed(self) -> None:
        mode = self.policy_combo.currentData()
        self.seed_spin.setEnabled(mode == "random")

    def tokens(self) -> List[str]:
        raw = self.order_edit.text().strip().replace(",", " ")
        return [tok.upper() for tok in raw.split() if tok.strip()]

    def refresh_preview(self) -> None:
        tokens = self.tokens()
        self.preview_list.clear()
        allowed = set(self.allowed_symbols)
        for token in tokens:
            label = token
            if token not in allowed:
                label += " • " + T(self.lang, "Unknown token")
            item = QListWidgetItem(label)
            if token not in allowed:
                item.setData(Qt.UserRole, "error")
            self.preview_list.addItem(item)

    def _load_preset(self, preset: CustomOrderPreset) -> None:
        self.name_edit.setText(preset.name)
        self.order_edit.setText(" ".join(preset.order))
        idx = self.policy_combo.findData(preset.policy.mode)
        if idx >= 0:
            self.policy_combo.setCurrentIndex(idx)
        if preset.policy.mode == "random" and preset.policy.seed is not None:
            self.seed_spin.setValue(preset.policy.seed)
            self.seed_spin.setEnabled(True)
        idx = self.length_combo.findData(preset.length_policy)
        if idx >= 0:
            self.length_combo.setCurrentIndex(idx)
        idx = self.missing_combo.findData(preset.on_missing_symbol)
        if idx >= 0:
            self.missing_combo.setCurrentIndex(idx)

    def build_preset(self) -> CustomOrderPreset:
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError(T(self.lang, "Preset name required"))
        tokens = self.tokens()
        if not tokens:
            raise ValueError(T(self.lang, "Order cannot be empty"))
        preset = CustomOrderPreset(
            name=name,
            symbols=self.allowed_symbols,
            order=tokens,
            policy=SelectionPolicy(
                mode=str(self.policy_combo.currentData()),
                seed=self.seed_spin.value() if self.seed_spin.isEnabled() else None,
            ),
            length_policy=str(self.length_combo.currentData()),
            on_missing_symbol=str(self.missing_combo.currentData()),
        )
        preset.validate()
        return preset

    def accept(self) -> None:  # type: ignore[override]
        try:
            self._result = self.build_preset()
        except Exception as exc:
            QMessageBox.warning(self, T(self.lang, "Edit Preset"), str(exc))
            return
        super().accept()

    def result(self) -> CustomOrderPreset | None:
        return self._result


class CustomPreviewDialog(QDialog):
    def __init__(
        self,
        lang: str,
        items: Sequence[PreviewItem],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle(T(self.lang, "Preview"))
        self.setMinimumWidth(440)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for idx, item in enumerate(items, start=1):
            if item.path is None:
                label = T(
                    self.lang,
                    "{i}. {symbol} – (skipped)",
                    i=idx,
                    symbol=item.token,
                )
            else:
                label = T(
                    self.lang,
                    "{i}. {symbol} – {path}",
                    i=idx,
                    symbol=item.token,
                    path=str(item.path),
                )
            self.list_widget.addItem(QListWidgetItem(label))
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

