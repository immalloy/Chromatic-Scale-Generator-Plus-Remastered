from __future__ import annotations

"""Primary Qt window for the Chromatic Scale Generator PLUS!"""

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QRadioButton,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T, list_languages

from .constants import (
    APP_ICON_PATH,
    APP_TITLE,
    MAX_GAP_SEC,
    MAX_SEMITONES,
    NOTE_NAMES,
    OCTAVES,
    PROJECT_TUTORIAL_URL,
    PROJECT_WIKI_URL,
)
from .custom_order import (
    DEFAULT_SYMBOLS,
    CustomOrderPreset,
    CustomTemplate,
    PresetError,
    ResolutionError,
    ResolutionResult,
    SelectionPolicy,
    build_default_sequence,
    export_preset,
    export_template,
    import_preset,
    import_template,
    resolve_sequence,
    scan_symbol_buckets,
)
from .dialogs import CreditsDialog, CustomPreviewDialog, PresetEditorDialog
from .generation import GenerateWorker
from .styles import build_stylesheet


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.lang = "en"
        self.mode = "dark"
        self.accent = "pink"

        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1040, 680)

        try:
            if os.path.exists(APP_ICON_PATH):
                self.setWindowIcon(QIcon(APP_ICON_PATH))
        except Exception:  # pragma: no cover - environment specific
            pass

        central = QWidget()
        self.setCentralWidget(central)

        self.cfg_group = QGroupBox(T(self.lang, "Configuration"))
        cfg_layout = QVBoxLayout(self.cfg_group)

        self.config_tabs = QTabWidget()
        cfg_layout.addWidget(self.config_tabs, 1)

        self.settings_tab = QWidget()
        settings_layout = QGridLayout(self.settings_tab)
        settings_layout.setContentsMargins(12, 12, 12, 12)
        settings_layout.setColumnStretch(1, 1)

        self.custom_tab = QWidget()
        custom_layout = QGridLayout(self.custom_tab)
        custom_layout.setContentsMargins(12, 12, 12, 12)
        custom_layout.setColumnStretch(1, 1)

        self.settings_tab_index = self.config_tabs.addTab(
            self.settings_tab, T(self.lang, "ConfigTabSettings")
        )
        self.custom_tab_index = self.config_tabs.addTab(
            self.custom_tab, T(self.lang, "ConfigTabCustom")
        )

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(
            T(self.lang, "Select a folder containing 1.wav, 2.wav, ...")
        )
        self.browse_btn = QPushButton(T(self.lang, "Browse…"))
        self.browse_btn.clicked.connect(self.choose_folder)

        self.warn_label = QLabel("")
        self.warn_label.setObjectName("WarnLabel")
        self.warn_label.setVisible(False)

        self.note_combo = QComboBox()
        self.note_combo.addItems(NOTE_NAMES)
        self.note_combo.setCurrentIndex(0)

        self.octave_combo = QComboBox()
        for octave in OCTAVES:
            self.octave_combo.addItem(str(octave))
        self.octave_combo.setCurrentText("3")

        self.range_spin = QSpinBox()
        self.range_spin.setRange(1, MAX_SEMITONES)
        self.range_spin.setValue(36)

        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0.0, MAX_GAP_SEC)
        self.gap_spin.setDecimals(3)
        self.gap_spin.setSingleStep(0.05)
        self.gap_spin.setValue(0.30)

        self.opt_pitched = QCheckBox(T(self.lang, "Apply pitch transformation"))
        self.opt_pitched.setChecked(True)
        self.opt_dump = QCheckBox(T(self.lang, "Dump individual pitched samples"))
        self.opt_random = QCheckBox(T(self.lang, "Randomize sample selection"))
        self.opt_random.setVisible(False)
        self.opt_normalize = QCheckBox(
            T(self.lang, "Peak normalize each sample (pre-pitch)")
        )
        self.opt_slicex_markers = QCheckBox(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )

        self.mode_label = QLabel(T(self.lang, "ModeLabel"))
        self.mode_normal_radio = QRadioButton(T(self.lang, "ModeNormal"))
        self.mode_random_radio = QRadioButton(T(self.lang, "ModeRandom"))
        self.mode_custom_radio = QRadioButton(T(self.lang, "ModeCustom"))
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.mode_normal_radio)
        self.mode_group.addButton(self.mode_random_radio)
        self.mode_group.addButton(self.mode_custom_radio)
        self.mode_normal_radio.setChecked(True)

        self.preset_label = QLabel(T(self.lang, "PresetLabel"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem(T(self.lang, "PresetNone"), None)
        custom_layout.addWidget(self.preset_label, 0, 0)
        custom_layout.addWidget(self.preset_combo, 0, 1, 1, 3)

        self.preset_new_btn = QPushButton(T(self.lang, "PresetNew"))
        self.preset_edit_btn = QPushButton(T(self.lang, "PresetEdit"))
        self.preset_save_as_btn = QPushButton(T(self.lang, "PresetSaveAs"))
        self.preset_delete_btn = QPushButton(T(self.lang, "PresetDelete"))
        self.preset_import_btn = QPushButton(T(self.lang, "PresetImport"))
        self.preset_export_btn = QPushButton(T(self.lang, "PresetExport"))

        button_row = QHBoxLayout()
        button_row.addWidget(self.preset_new_btn)
        button_row.addWidget(self.preset_edit_btn)
        button_row.addWidget(self.preset_save_as_btn)
        button_row.addWidget(self.preset_delete_btn)
        button_row.addWidget(self.preset_import_btn)
        button_row.addWidget(self.preset_export_btn)
        button_row.addStretch(1)
        custom_layout.addLayout(button_row, 1, 0, 1, 4)

        self.selection_label = QLabel(T(self.lang, "Selection policy"))
        self.selection_combo = QComboBox()
        self.selection_combo.addItem(T(self.lang, "SelectionFirst"), "first")
        self.selection_combo.addItem(T(self.lang, "SelectionCycle"), "cycle")
        self.selection_combo.addItem(T(self.lang, "SelectionRandom"), "random")
        self.selection_seed = QSpinBox()
        self.selection_seed.setRange(0, 999999)
        self.selection_seed.setEnabled(False)
        custom_layout.addWidget(self.selection_label, 2, 0)
        seed_row = QHBoxLayout()
        seed_row.addWidget(self.selection_combo)
        seed_row.addWidget(self.selection_seed)
        custom_layout.addLayout(seed_row, 2, 1, 1, 3)
        self.selection_combo.setCurrentIndex(0)

        self.length_label = QLabel(T(self.lang, "Length handling"))
        self.length_combo = QComboBox()
        self.length_combo.addItem(T(self.lang, "LengthPad"), "pad")
        self.length_combo.addItem(T(self.lang, "LengthTruncate"), "truncate")
        self.length_combo.addItem(T(self.lang, "LengthError"), "error")
        custom_layout.addWidget(self.length_label, 3, 0)
        custom_layout.addWidget(self.length_combo, 3, 1, 1, 3)
        self.length_combo.setCurrentIndex(0)

        self.missing_label = QLabel(T(self.lang, "Missing symbol"))
        self.missing_combo = QComboBox()
        self.missing_combo.addItem(T(self.lang, "MissingSkip"), "skip")
        self.missing_combo.addItem(T(self.lang, "MissingAsk"), "ask")
        self.missing_combo.addItem(T(self.lang, "MissingError"), "error")
        custom_layout.addWidget(self.missing_label, 4, 0)
        custom_layout.addWidget(self.missing_combo, 4, 1, 1, 3)
        self.missing_combo.setCurrentIndex(0)

        self.preview_btn = QPushButton(T(self.lang, "Preview"))
        custom_layout.addWidget(self.preview_btn, 5, 0)

        self.template_save_btn = QPushButton(T(self.lang, "TemplateSave"))
        self.template_load_btn = QPushButton(T(self.lang, "TemplateLoad"))
        self.template_import_btn = QPushButton(T(self.lang, "TemplateImport"))
        self.template_export_btn = QPushButton(T(self.lang, "TemplateExport"))

        template_row = QHBoxLayout()
        template_row.addWidget(self.template_save_btn)
        template_row.addWidget(self.template_load_btn)
        template_row.addWidget(self.template_import_btn)
        template_row.addWidget(self.template_export_btn)
        template_row.addStretch(1)
        custom_layout.addLayout(template_row, 5, 1, 1, 3)

        self.config_tabs.setTabEnabled(self.custom_tab_index, False)
        self.custom_tab.setEnabled(False)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["dark", "light"])
        self.mode_combo.setCurrentText(self.mode)

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["blue", "pink"])
        self.accent_combo.setCurrentText(self.accent)

        self.lang_combo = QComboBox()
        for code, label in list_languages():
            self.lang_combo.addItem(label, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData("en"))

        row = 0
        self.sample_folder_label = QLabel(T(self.lang, "Sample folder"))
        settings_layout.addWidget(self.sample_folder_label, row, 0)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.path_edit, 1)
        folder_row.addWidget(self.browse_btn, 0)
        settings_layout.addLayout(folder_row, row, 1)
        row += 1

        settings_layout.addWidget(self.warn_label, row, 0, 1, 2)
        row += 1

        self.starting_note_label = QLabel(T(self.lang, "Starting note"))
        settings_layout.addWidget(self.starting_note_label, row, 0)
        settings_layout.addWidget(self.note_combo, row, 1)
        row += 1

        self.starting_octave_label = QLabel(T(self.lang, "Starting octave"))
        settings_layout.addWidget(self.starting_octave_label, row, 0)
        settings_layout.addWidget(self.octave_combo, row, 1)
        row += 1

        self.semitone_range_label = QLabel(T(self.lang, "Semitone range"))
        settings_layout.addWidget(self.semitone_range_label, row, 0)
        settings_layout.addWidget(self.range_spin, row, 1)
        row += 1

        self.gap_label = QLabel(T(self.lang, "Gap (seconds)"))
        settings_layout.addWidget(self.gap_label, row, 0)
        settings_layout.addWidget(self.gap_spin, row, 1)
        row += 1

        settings_layout.addWidget(self.opt_pitched, row, 0, 1, 2)
        row += 1

        settings_layout.addWidget(self.opt_dump, row, 0, 1, 2)
        row += 1

        mode_row = QHBoxLayout()
        mode_row.addWidget(self.mode_label)
        mode_row.addWidget(self.mode_normal_radio)
        mode_row.addWidget(self.mode_random_radio)
        mode_row.addWidget(self.mode_custom_radio)
        mode_row.addStretch(1)
        settings_layout.addLayout(mode_row, row, 0, 1, 2)
        row += 1

        settings_layout.addWidget(self.opt_normalize, row, 0, 1, 2)
        row += 1

        settings_layout.addWidget(self.opt_slicex_markers, row, 0, 1, 2)
        row += 1

        appearance_row = QHBoxLayout()
        self.theme_label = QLabel(T(self.lang, "Theme:"))
        appearance_row.addWidget(self.theme_label)
        appearance_row.addWidget(self.mode_combo)
        appearance_row.addSpacing(12)
        self.accent_label = QLabel(T(self.lang, "Accent:"))
        appearance_row.addWidget(self.accent_label)
        appearance_row.addWidget(self.accent_combo)
        appearance_row.addSpacing(12)
        self.language_label = QLabel(T(self.lang, "Language:"))
        appearance_row.addWidget(self.language_label)
        appearance_row.addWidget(self.lang_combo)
        appearance_row.addStretch(1)
        settings_layout.addLayout(appearance_row, row, 0, 1, 2)
        row += 1

        settings_layout.setRowStretch(row, 1)

        self.run_group = QGroupBox(T(self.lang, "Run"))
        run_layout = QVBoxLayout(self.run_group)

        btns_row = QHBoxLayout()
        self.generate_btn = QPushButton(T(self.lang, "Generate Chromatic"))
        self.generate_btn.setEnabled(False)
        self.cancel_btn = QPushButton(T(self.lang, "Cancel"))
        self.cancel_btn.setEnabled(False)
        self.open_out_btn = QPushButton(T(self.lang, "Open Output Folder"))
        self.open_out_btn.setEnabled(False)
        btns_row.addWidget(self.generate_btn)
        btns_row.addWidget(self.cancel_btn)
        btns_row.addWidget(self.open_out_btn)
        run_layout.addLayout(btns_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(T(self.lang, "Logs will appear here…"))

        run_layout.addWidget(self.progress)
        run_layout.addWidget(self.log, 1)

        footer_row = QHBoxLayout()
        self.footer = QLabel(T(self.lang, "Footer"))
        self.footer.setObjectName("Footer")
        self.wiki_btn = QPushButton(T(self.lang, "Wiki"))
        self.wiki_btn.setObjectName("LinkButton")
        self.tutorial_btn = QPushButton(T(self.lang, "Tutorial"))
        self.tutorial_btn.setObjectName("LinkButton")
        self.credits_btn = QPushButton(T(self.lang, "Credits"))
        self.credits_btn.setObjectName("LinkButton")
        footer_row.addWidget(self.footer, 1)
        footer_row.addStretch(1)
        footer_row.addWidget(self.wiki_btn, 0)
        footer_row.addWidget(self.tutorial_btn, 0)
        footer_row.addWidget(self.credits_btn, 0)

        outer = QVBoxLayout(central)
        inner = QHBoxLayout()
        inner.addWidget(self.cfg_group, 1)
        inner.addWidget(self.run_group, 1)
        outer.addLayout(inner, 1)
        outer.addLayout(footer_row)

        help_menu = self.menuBar().addMenu(T(self.lang, "&Help"))
        act_wiki = QAction(T(self.lang, "Wiki"), self)
        act_wiki.triggered.connect(self.open_wiki)
        help_menu.addAction(act_wiki)

        act_tutorial = QAction(T(self.lang, "Tutorial"), self)
        act_tutorial.triggered.connect(self.open_tutorial)
        help_menu.addAction(act_tutorial)

        help_menu.addSeparator()

        act_credits = QAction(T(self.lang, "Credits"), self)
        act_credits.triggered.connect(self.show_credits)
        help_menu.addAction(act_credits)

        self.setStatusBar(QStatusBar())
        self.apply_theme()

        self.path_edit.textChanged.connect(self.refresh_validation)
        self.mode_combo.currentTextChanged.connect(self.on_theme_changed)
        self.accent_combo.currentTextChanged.connect(self.on_theme_changed)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        self.generate_btn.clicked.connect(self.start_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.open_out_btn.clicked.connect(self.open_output_folder_clicked)
        self.wiki_btn.clicked.connect(self.open_wiki)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        self.credits_btn.clicked.connect(self.show_credits)
        self.mode_normal_radio.toggled.connect(self.on_mode_selection_changed)
        self.mode_random_radio.toggled.connect(self.on_mode_selection_changed)
        self.mode_custom_radio.toggled.connect(self.on_mode_selection_changed)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        self.preset_new_btn.clicked.connect(self.on_preset_new)
        self.preset_edit_btn.clicked.connect(self.on_preset_edit)
        self.preset_save_as_btn.clicked.connect(self.on_preset_save_as)
        self.preset_delete_btn.clicked.connect(self.on_preset_delete)
        self.preset_import_btn.clicked.connect(self.on_preset_import)
        self.preset_export_btn.clicked.connect(self.on_preset_export)
        self.selection_combo.currentIndexChanged.connect(
            self.on_selection_policy_changed
        )
        self.selection_seed.valueChanged.connect(self.on_selection_seed_changed)
        self.length_combo.currentIndexChanged.connect(self.on_length_policy_changed)
        self.missing_combo.currentIndexChanged.connect(self.on_missing_policy_changed)
        self.preview_btn.clicked.connect(self.on_preview_clicked)
        self.template_save_btn.clicked.connect(self.on_template_save)
        self.template_load_btn.clicked.connect(self.on_template_load)
        self.template_import_btn.clicked.connect(self.on_template_import)
        self.template_export_btn.clicked.connect(self.on_template_export)

        self.worker: GenerateWorker | None = None
        self.last_output_path: Path | None = None
        self.current_mode = "normal"
        self.custom_presets: dict[str, CustomOrderPreset] = {}
        self.active_preset: CustomOrderPreset | None = None
        self.custom_templates: dict[str, CustomTemplate] = {}
        self.last_resolution: ResolutionResult | None = None

        self.setAcceptDrops(True)
        self.refresh_validation()
        self.refresh_button_state()

    def apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.mode, self.accent))

    def on_theme_changed(self) -> None:
        self.mode = self.mode_combo.currentText()
        self.accent = self.accent_combo.currentText()
        self.apply_theme()

    def on_language_changed(self) -> None:
        code = self.lang_combo.currentData()
        if code and code != self.lang:
            self.lang = code
            self.retranslate_all()

    def retranslate_all(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.cfg_group.setTitle(T(self.lang, "Configuration"))
        self.config_tabs.setTabText(
            self.settings_tab_index, T(self.lang, "ConfigTabSettings")
        )
        self.config_tabs.setTabText(
            self.custom_tab_index, T(self.lang, "ConfigTabCustom")
        )
        self.run_group.setTitle(T(self.lang, "Run"))
        self.sample_folder_label.setText(T(self.lang, "Sample folder"))
        self.starting_note_label.setText(T(self.lang, "Starting note"))
        self.starting_octave_label.setText(T(self.lang, "Starting octave"))
        self.semitone_range_label.setText(T(self.lang, "Semitone range"))
        self.gap_label.setText(T(self.lang, "Gap (seconds)"))
        self.browse_btn.setText(T(self.lang, "Browse…"))
        self.path_edit.setPlaceholderText(
            T(self.lang, "Select a folder containing 1.wav, 2.wav, ...")
        )
        self.opt_pitched.setText(T(self.lang, "Apply pitch transformation"))
        self.opt_dump.setText(T(self.lang, "Dump individual pitched samples"))
        self.opt_random.setText(T(self.lang, "Randomize sample selection"))
        self.opt_normalize.setText(
            T(self.lang, "Peak normalize each sample (pre-pitch)")
        )
        self.opt_slicex_markers.setText(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )
        self.mode_label.setText(T(self.lang, "ModeLabel"))
        self.mode_normal_radio.setText(T(self.lang, "ModeNormal"))
        self.mode_random_radio.setText(T(self.lang, "ModeRandom"))
        self.mode_custom_radio.setText(T(self.lang, "ModeCustom"))
        self.preset_label.setText(T(self.lang, "PresetLabel"))
        self.preset_new_btn.setText(T(self.lang, "PresetNew"))
        self.preset_edit_btn.setText(T(self.lang, "PresetEdit"))
        self.preset_save_as_btn.setText(T(self.lang, "PresetSaveAs"))
        self.preset_delete_btn.setText(T(self.lang, "PresetDelete"))
        self.preset_import_btn.setText(T(self.lang, "PresetImport"))
        self.preset_export_btn.setText(T(self.lang, "PresetExport"))
        self.preset_combo.setItemText(0, T(self.lang, "PresetNone"))
        self.selection_label.setText(T(self.lang, "Selection policy"))
        self.selection_combo.setItemText(0, T(self.lang, "SelectionFirst"))
        self.selection_combo.setItemText(1, T(self.lang, "SelectionCycle"))
        self.selection_combo.setItemText(2, T(self.lang, "SelectionRandom"))
        self.length_label.setText(T(self.lang, "Length handling"))
        self.length_combo.setItemText(0, T(self.lang, "LengthPad"))
        self.length_combo.setItemText(1, T(self.lang, "LengthTruncate"))
        self.length_combo.setItemText(2, T(self.lang, "LengthError"))
        self.missing_label.setText(T(self.lang, "Missing symbol"))
        self.missing_combo.setItemText(0, T(self.lang, "MissingSkip"))
        self.missing_combo.setItemText(1, T(self.lang, "MissingAsk"))
        self.missing_combo.setItemText(2, T(self.lang, "MissingError"))
        self.preview_btn.setText(T(self.lang, "Preview"))
        self.template_save_btn.setText(T(self.lang, "TemplateSave"))
        self.template_load_btn.setText(T(self.lang, "TemplateLoad"))
        self.template_import_btn.setText(T(self.lang, "TemplateImport"))
        self.template_export_btn.setText(T(self.lang, "TemplateExport"))
        self.generate_btn.setText(T(self.lang, "Generate Chromatic"))
        self.cancel_btn.setText(T(self.lang, "Cancel"))
        self.open_out_btn.setText(T(self.lang, "Open Output Folder"))
        self.theme_label.setText(T(self.lang, "Theme:"))
        self.accent_label.setText(T(self.lang, "Accent:"))
        self.language_label.setText(T(self.lang, "Language:"))
        self.wiki_btn.setText(T(self.lang, "Wiki"))
        self.tutorial_btn.setText(T(self.lang, "Tutorial"))
        self.credits_btn.setText(T(self.lang, "Credits"))
        self.footer.setText(T(self.lang, "Footer"))

        self.menuBar().clear()
        help_menu = self.menuBar().addMenu(T(self.lang, "&Help"))
        act_wiki = QAction(T(self.lang, "Wiki"), self)
        act_wiki.triggered.connect(self.open_wiki)
        help_menu.addAction(act_wiki)

        act_tutorial = QAction(T(self.lang, "Tutorial"), self)
        act_tutorial.triggered.connect(self.open_tutorial)
        help_menu.addAction(act_tutorial)

        help_menu.addSeparator()

        act_credits = QAction(T(self.lang, "Credits"), self)
        act_credits.triggered.connect(self.show_credits)
        help_menu.addAction(act_credits)

        self.refresh_validation()

    def on_mode_selection_changed(self) -> None:
        if self.mode_normal_radio.isChecked():
            self.current_mode = "normal"
        elif self.mode_random_radio.isChecked():
            self.current_mode = "random"
        else:
            self.current_mode = "custom"
        enable_custom = self.current_mode == "custom"
        self.custom_tab.setEnabled(enable_custom)
        self.config_tabs.setTabEnabled(self.custom_tab_index, enable_custom)
        if enable_custom:
            self.config_tabs.setCurrentIndex(self.custom_tab_index)
        elif self.config_tabs.currentIndex() == self.custom_tab_index:
            self.config_tabs.setCurrentIndex(self.settings_tab_index)
        self.selection_seed.setEnabled(
            enable_custom
            and self.selection_combo.currentData() == "random"
        )
        self.opt_random.setChecked(self.current_mode == "random")
        self.refresh_button_state()

    def refresh_preset_combo(self, select: str | None = None) -> None:
        if select is None and self.active_preset:
            select = self.active_preset.name
        self.preset_combo.blockSignals(True)
        current_index = self.preset_combo.currentIndex()
        self.preset_combo.clear()
        self.preset_combo.addItem(T(self.lang, "PresetNone"), None)
        for name in sorted(self.custom_presets.keys(), key=str.casefold):
            self.preset_combo.addItem(name, name)
        self.preset_combo.blockSignals(False)
        if select:
            idx = self.preset_combo.findData(select)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
            else:
                self.preset_combo.setCurrentIndex(0)
        else:
            self.preset_combo.setCurrentIndex(min(current_index, self.preset_combo.count() - 1))
        self.on_preset_changed()

    def set_active_preset(self, preset: CustomOrderPreset | None) -> None:
        self.active_preset = preset
        block_sel = self.selection_combo.blockSignals(True)
        block_len = self.length_combo.blockSignals(True)
        block_miss = self.missing_combo.blockSignals(True)
        try:
            if preset is None:
                self.selection_combo.setCurrentIndex(0)
                self.selection_seed.setValue(0)
                self.selection_seed.setEnabled(False)
                self.length_combo.setCurrentIndex(0)
                self.missing_combo.setCurrentIndex(0)
            else:
                idx = self.selection_combo.findData(preset.policy.mode)
                if idx >= 0:
                    self.selection_combo.setCurrentIndex(idx)
                if preset.policy.seed is not None:
                    self.selection_seed.setValue(int(preset.policy.seed))
                self.selection_seed.setEnabled(
                    self.current_mode == "custom"
                    and self.selection_combo.currentData() == "random"
                )
                idx = self.length_combo.findData(preset.length_policy)
                if idx >= 0:
                    self.length_combo.setCurrentIndex(idx)
                idx = self.missing_combo.findData(preset.on_missing_symbol)
                if idx >= 0:
                    self.missing_combo.setCurrentIndex(idx)
        finally:
            self.selection_combo.blockSignals(block_sel)
            self.length_combo.blockSignals(block_len)
            self.missing_combo.blockSignals(block_miss)
        self.refresh_button_state()

    def on_preset_changed(self) -> None:
        data = self.preset_combo.currentData()
        if data is None:
            self.set_active_preset(None)
            return
        preset = self.custom_presets.get(data)
        if preset:
            self.set_active_preset(preset)

    def clone_preset(self, preset: CustomOrderPreset) -> CustomOrderPreset:
        return CustomOrderPreset(
            name=preset.name,
            symbols=list(preset.symbols),
            order=list(preset.order),
            policy=SelectionPolicy(
                mode=preset.policy.mode,
                seed=preset.policy.seed,
            ),
            length_policy=preset.length_policy,
            on_missing_symbol=preset.on_missing_symbol,
        )

    def on_preset_new(self) -> None:
        dialog = PresetEditorDialog(self.lang, DEFAULT_SYMBOLS, parent=self)
        if dialog.exec() == QDialog.Accepted:
            preset = dialog.result()
            if preset:
                self.custom_presets[preset.name] = preset
                self.refresh_preset_combo(select=preset.name)

    def on_preset_edit(self) -> None:
        if not self.active_preset:
            self.show_info(T(self.lang, "PresetSelectPrompt"))
            return
        dialog = PresetEditorDialog(
            self.lang,
            self.active_preset.symbols,
            preset=self.clone_preset(self.active_preset),
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            preset = dialog.result()
            if preset:
                self.custom_presets.pop(self.active_preset.name, None)
                self.custom_presets[preset.name] = preset
                self.refresh_preset_combo(select=preset.name)

    def on_preset_save_as(self) -> None:
        if not self.active_preset:
            self.show_info(T(self.lang, "PresetSelectPrompt"))
            return
        clone = self.clone_preset(self.active_preset)
        clone.name = clone.name + " Copy"
        dialog = PresetEditorDialog(
            self.lang,
            clone.symbols,
            preset=clone,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            preset = dialog.result()
            if preset:
                self.custom_presets[preset.name] = preset
                self.refresh_preset_combo(select=preset.name)

    def on_preset_delete(self) -> None:
        data = self.preset_combo.currentData()
        if data is None:
            return
        if not self.ask_yes_no(
            APP_TITLE,
            T(self.lang, "PresetDeleteConfirm", name=str(data)),
        ):
            return
        self.custom_presets.pop(str(data), None)
        self.refresh_preset_combo(select=None)

    def on_preset_import(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            T(self.lang, "PresetImportTitle"),
            str(self.path_edit.text() or Path.home()),
            "Custom Order (*.csgorder.json)",
        )
        if not filename:
            return
        try:
            preset = import_preset(Path(filename))
        except Exception as exc:
            self.show_error(str(exc))
            return
        self.custom_presets[preset.name] = preset
        self.refresh_preset_combo(select=preset.name)

    def on_preset_export(self) -> None:
        if not self.active_preset:
            self.show_info(T(self.lang, "PresetSelectPrompt"))
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            T(self.lang, "PresetExportTitle"),
            self.active_preset.name + ".csgorder.json",
            "Custom Order (*.csgorder.json)",
        )
        if not filename:
            return
        try:
            export_preset(self.active_preset, Path(filename))
        except Exception as exc:
            self.show_error(str(exc))

    def on_selection_policy_changed(self) -> None:
        mode = self.selection_combo.currentData()
        self.selection_seed.setEnabled(
            self.current_mode == "custom" and mode == "random"
        )
        if self.active_preset:
            self.active_preset.policy = SelectionPolicy(
                mode=str(mode),
                seed=self.selection_seed.value()
                if mode == "random"
                else None,
            )

    def on_selection_seed_changed(self, value: int) -> None:
        if self.active_preset and self.active_preset.policy.mode == "random":
            self.active_preset.policy = SelectionPolicy(
                mode=self.active_preset.policy.mode,
                seed=value,
            )

    def on_length_policy_changed(self) -> None:
        if self.active_preset:
            self.active_preset.length_policy = str(self.length_combo.currentData())

    def on_missing_policy_changed(self) -> None:
        if self.active_preset:
            self.active_preset.on_missing_symbol = str(
                self.missing_combo.currentData()
            )

    def resolve_current_preset(
        self, *, report: bool = True
    ) -> tuple[ResolutionResult, list[str]] | None:
        if not self.folder_valid():
            if report:
                self.show_error(
                    T(self.lang, "Invalid folder. Place '1.wav', '2.wav', ... in it.")
                )
            return None
        if not self.active_preset:
            if report:
                self.show_info(T(self.lang, "PresetSelectPrompt"))
            return None
        sample_path = Path(self.path_edit.text().strip())
        try:
            scan_result = scan_symbol_buckets(
                sample_path, allowed_symbols=self.active_preset.symbols
            )
            result = resolve_sequence(
                self.active_preset,
                scan_result.buckets,
                target_length=int(self.range_spin.value()),
            )
        except (PresetError, ResolutionError) as exc:
            if report:
                self.show_error(str(exc))
            return None
        self.last_resolution = result
        if report:
            for warning in scan_result.warnings:
                self.append_log(T(self.lang, "WarningLog", msg=warning))
        return result, scan_result.warnings

    def on_preview_clicked(self) -> None:
        resolved = self.resolve_current_preset(report=True)
        if not resolved:
            return
        result, _warnings = resolved
        dialog = CustomPreviewDialog(self.lang, result.preview, self)
        dialog.exec()

    def capture_settings(self) -> dict[str, object]:
        return {
            "note_index": self.note_combo.currentIndex(),
            "octave": int(self.octave_combo.currentText()),
            "semitones": int(self.range_spin.value()),
            "gap": float(self.gap_spin.value()),
            "pitched": self.opt_pitched.isChecked(),
            "dump": self.opt_dump.isChecked(),
            "normalize": self.opt_normalize.isChecked(),
            "slicex": self.opt_slicex_markers.isChecked(),
            "mode": self.current_mode,
            "preset": self.active_preset.name if self.active_preset else None,
        }

    def apply_settings(self, settings: dict[str, object]) -> None:
        note_index = int(settings.get("note_index", self.note_combo.currentIndex()))
        if 0 <= note_index < self.note_combo.count():
            self.note_combo.setCurrentIndex(note_index)
        octave = settings.get("octave")
        if octave is not None:
            self.octave_combo.setCurrentText(str(int(octave)))
        semitones = int(settings.get("semitones", self.range_spin.value()))
        self.range_spin.setValue(semitones)
        gap = settings.get("gap")
        if gap is not None:
            self.gap_spin.setValue(float(gap))
        self.opt_pitched.setChecked(bool(settings.get("pitched", True)))
        self.opt_dump.setChecked(bool(settings.get("dump", False)))
        self.opt_normalize.setChecked(bool(settings.get("normalize", False)))
        self.opt_slicex_markers.setChecked(bool(settings.get("slicex", False)))
        mode = settings.get("mode", "normal")
        if mode == "random":
            self.mode_random_radio.setChecked(True)
        elif mode == "custom":
            self.mode_custom_radio.setChecked(True)
        else:
            self.mode_normal_radio.setChecked(True)
        preset_name = settings.get("preset")
        if isinstance(preset_name, str) and preset_name in self.custom_presets:
            idx = self.preset_combo.findData(preset_name)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def on_template_save(self) -> None:
        if not self.active_preset:
            self.show_info(T(self.lang, "PresetSelectPrompt"))
            return
        name, ok = QInputDialog.getText(
            self,
            T(self.lang, "TemplateSaveTitle"),
            T(self.lang, "TemplateNamePrompt"),
        )
        if not ok or not name.strip():
            return
        template = CustomTemplate(
            name=name.strip(),
            preset=self.clone_preset(self.active_preset),
            settings=self.capture_settings(),
        )
        self.custom_templates[template.name] = template
        self.show_info(T(self.lang, "TemplateSaved", name=template.name))

    def apply_template(self, template: CustomTemplate) -> None:
        self.custom_presets[template.preset.name] = template.preset
        self.refresh_preset_combo(select=template.preset.name)
        self.apply_settings(template.settings)

    def on_template_load(self) -> None:
        if not self.custom_templates:
            self.show_info(T(self.lang, "TemplateNone"))
            return
        names = sorted(self.custom_templates.keys(), key=str.casefold)
        name, ok = QInputDialog.getItem(
            self,
            T(self.lang, "TemplateLoadTitle"),
            T(self.lang, "TemplateChoosePrompt"),
            names,
            0,
            False,
        )
        if not ok or not name:
            return
        template = self.custom_templates.get(name)
        if template:
            self.apply_template(template)

    def on_template_import(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            T(self.lang, "TemplateImportTitle"),
            str(self.path_edit.text() or Path.home()),
            "Templates (*.csgtemplate.json)",
        )
        if not filename:
            return
        try:
            template = import_template(Path(filename))
        except Exception as exc:
            self.show_error(str(exc))
            return
        self.custom_templates[template.name] = template
        self.apply_template(template)
        self.show_info(T(self.lang, "TemplateImported", name=template.name))

    def on_template_export(self) -> None:
        if not self.custom_templates:
            self.show_info(T(self.lang, "TemplateNone"))
            return
        names = sorted(self.custom_templates.keys(), key=str.casefold)
        name, ok = QInputDialog.getItem(
            self,
            T(self.lang, "TemplateExportTitle"),
            T(self.lang, "TemplateChoosePrompt"),
            names,
            0,
            False,
        )
        if not ok or not name:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            T(self.lang, "TemplateExportTitle"),
            name + ".csgtemplate.json",
            "Templates (*.csgtemplate.json)",
        )
        if not filename:
            return
        template = self.custom_templates.get(name)
        if not template:
            return
        try:
            export_template(template, Path(filename))
        except Exception as exc:
            self.show_error(str(exc))

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if os.path.isdir(path):
            self.path_edit.setText(path)

    def show_error(self, msg: str) -> None:
        QMessageBox.critical(self, APP_TITLE, msg)

    def show_info(self, msg: str) -> None:
        QMessageBox.information(self, APP_TITLE, msg)

    def ask_yes_no(self, title: str, question: str) -> bool:
        ret = QMessageBox.question(
            self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        return ret == QMessageBox.Yes

    def folder_valid(self) -> bool:
        path = Path(self.path_edit.text().strip())
        return path.exists() and path.is_dir() and (path / "1.wav").exists()

    def refresh_validation(self) -> None:
        text = self.path_edit.text().strip()
        if not text:
            self.warn_label.setVisible(False)
        else:
            path = Path(text)
            if not path.exists() or not path.is_dir():
                self.warn_label.setText(T(self.lang, "Folder not found."))
                self.warn_label.setVisible(True)
            elif not (path / "1.wav").exists():
                self.warn_label.setText(
                    T(self.lang, "Need at least 1.wav in this folder.")
                )
                self.warn_label.setVisible(True)
            else:
                idx = 1
                while (path / f"{idx}.wav").exists():
                    idx += 1
                if idx == 1:
                    self.warn_label.setText(
                        T(self.lang, "No sequential samples found (1.wav, 2.wav, ...).")
                    )
                    self.warn_label.setVisible(True)
                else:
                    self.warn_label.setVisible(False)
        self.refresh_button_state()

    def refresh_button_state(self) -> None:
        ok = (
            self.folder_valid()
            and self.range_spin.value() > 0
            and (0.0 <= self.gap_spin.value() <= MAX_GAP_SEC)
        )
        if self.current_mode == "custom":
            ok = ok and self.active_preset is not None
        self.generate_btn.setEnabled(ok and (self.worker is None))
        self.cancel_btn.setEnabled(self.worker is not None)
        self.open_out_btn.setEnabled(
            self.last_output_path is not None
            and os.path.exists(self.last_output_path)
        )

    def choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, T(self.lang, "Select Sample Folder"), os.path.expanduser("~")
        )
        if path:
            self.path_edit.setText(path)
            self.statusBar().showMessage(
                T(self.lang, "Selected folder: {p}", p=path), 5000
            )

    def open_output_folder_clicked(self) -> None:
        if not self.last_output_path or not os.path.exists(self.last_output_path):
            self.show_info(T(self.lang, "No output file yet."))
            return
        self.open_output_folder(self.last_output_path)

    def open_output_folder(self, filepath: str | Path) -> None:
        fp = str(filepath)
        if os.path.exists(fp):
            try:
                subprocess.Popen(f'explorer /select,"{fp}"')
            except Exception:  # pragma: no cover - OS specific
                subprocess.Popen(["explorer", os.path.dirname(fp)])

    def show_credits(self) -> None:
        dialog = CreditsDialog(self.lang, self)
        dialog.exec()

    def open_wiki(self) -> None:
        QDesktopServices.openUrl(QUrl(PROJECT_WIKI_URL))

    def open_tutorial(self) -> None:
        QDesktopServices.openUrl(QUrl(PROJECT_TUTORIAL_URL))

    @Slot()
    def start_generation(self) -> None:
        if not self.folder_valid():
            self.show_error(
                T(self.lang, "Invalid folder. Place '1.wav', '2.wav', ... in it.")
            )
            return

        sample_path = Path(self.path_edit.text().strip())
        out_path = sample_path / "chromatic.wav"

        if out_path.exists() and not self.ask_yes_no(
            APP_TITLE,
            T(self.lang, "'{name}' already exists. Overwrite?", name=out_path.name),
        ):
            self.statusBar().showMessage(T(self.lang, "Cancelled by user."), 5000)
            return

        semitones = int(self.range_spin.value())
        gap_seconds = float(self.gap_spin.value())
        pitched = self.opt_pitched.isChecked()
        dump_samples = self.opt_dump.isChecked()
        mode = self.current_mode
        randomize = mode == "random"
        normalize = self.opt_normalize.isChecked()
        slicex_markers = self.opt_slicex_markers.isChecked()
        start_note_index = self.note_combo.currentIndex()
        start_octave = int(self.octave_combo.currentText())

        custom_sequence: list[Path] | None = None
        if mode == "custom":
            resolved = self.resolve_current_preset(report=True)
            if not resolved:
                return
            result, _warnings = resolved
            custom_sequence = [Path(p) for p in result.sequence]
            if not custom_sequence:
                self.show_error(T(self.lang, "CustomSequenceEmpty"))
                return
            semitones = len(custom_sequence)
            if (
                self.active_preset
                and self.active_preset.length_policy == "truncate"
                and semitones != int(self.range_spin.value())
            ):
                self.append_log(
                    T(
                        self.lang,
                        "TruncateWarning",
                        requested=int(self.range_spin.value()),
                        actual=semitones,
                    )
                )

        self.log.clear()
        self.progress.setValue(0)

        self.worker = GenerateWorker(
            sample_path,
            semitones,
            gap_seconds,
            pitched,
            dump_samples,
            randomize,
            start_note_index,
            start_octave,
            normalize,
            slicex_markers,
            self.lang,
            mode=mode,
            custom_sequence=custom_sequence,
        )
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.finished.connect(self.on_worker_finished)

        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.open_out_btn.setEnabled(False)

        self.statusBar().showMessage(T(self.lang, "Generating…"))
        self.worker.start()

    @Slot()
    def cancel_generation(self) -> None:
        if self.worker:
            self.worker.request_cancel()
            self.statusBar().showMessage(T(self.lang, "Cancelling…"))

    @Slot(str)
    def append_log(self, text: str) -> None:
        self.log.append(text)
        self.log.moveCursor(QTextCursor.End)

    @Slot()
    def on_worker_finished(self) -> None:
        self.worker = None
        self.refresh_button_state()

    @Slot(str)
    def on_done(self, out_path: str) -> None:
        self.statusBar().showMessage(
            T(self.lang, "Done! Saved to {p}", p=out_path), 8000
        )
        self.append_log(T(self.lang, "✅ Completed! Output: {p}", p=out_path))
        self.progress.setValue(100)
        self.last_output_path = Path(out_path)
        self.open_out_btn.setEnabled(True)

    @Slot(str)
    def on_error(self, msg: str) -> None:
        self.statusBar().showMessage(T(self.lang, "An error occurred."), 8000)
        self.append_log(T(self.lang, "❌ Error: {m}", m=msg))
        self.show_error(msg)

    @Slot(str)
    def on_cancelled(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 8000)
        self.append_log(T(self.lang, "⚠️ Generation was cancelled."))
        self.progress.setValue(0)


__all__ = ["MainWindow"]
