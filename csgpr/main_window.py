from __future__ import annotations

"""Primary Qt window for the Chromatic Scale Generator PLUS!

UI layout overview
===================
* Header: branded title row with quick access actions (settings, wiki,
  tutorial, credits) and a descriptive tagline to orient new users.
* Main content splitter:
  - Sample setup card on the left for folder selection, musical range
    configuration, and processing toggles grouped into logical sections.
  - Generation status card on the right containing the run summary,
    progress indicator, log console, and action rows.
* Footer: project attribution string that stays visible regardless of
  window size for accessibility.

The redesign embraces a PC-first responsive layout, clear visual
hierarchy, and accessible affordances while retaining the app's core
functionality.
"""

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QSpinBox,
    QStatusBar,
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
from .dialogs import CreditsDialog, SettingsDialog
from .generation import GenerateWorker
from .styles import build_stylesheet


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.lang = "en"
        self.mode = "dark"
        self.accent = "pink"

        self._init_window()
        self._build_ui()
        self._connect_signals()

        self.build_menus()

        self.setStatusBar(QStatusBar())
        self.apply_theme()

        self.worker: GenerateWorker | None = None
        self.last_output_path: Path | None = None

        self.setAcceptDrops(True)
        self.refresh_validation()
        self.refresh_button_state()

    def _init_window(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1200, 760)

        try:
            if os.path.exists(APP_ICON_PATH):
                self.setWindowIcon(QIcon(APP_ICON_PATH))
        except Exception:  # pragma: no cover - environment specific
            pass

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(24)

        header = self._build_header()
        outer.addWidget(header)

        splitter = QSplitter()
        splitter.setObjectName("ContentSplitter")
        splitter.setChildrenCollapsible(False)

        config_panel = self._build_configuration_panel()
        status_panel = self._build_generation_panel()
        splitter.addWidget(config_panel)
        splitter.addWidget(status_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        outer.addWidget(splitter, 1)

        footer = self._build_footer()
        outer.addWidget(footer)

    def _build_header(self) -> QWidget:
        container = QFrame()
        container.setObjectName("HeaderFrame")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.hero_title_label = QLabel(T(self.lang, "WorkspaceHeadline"))
        self.hero_title_label.setObjectName("HeroTitle")
        self.hero_title_label.setAccessibleDescription(
            T(self.lang, "WorkspaceHeadline")
        )
        top_row.addWidget(self.hero_title_label, 1)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)

        self.settings_btn = QPushButton(T(self.lang, "Settings"))
        self.settings_btn.setObjectName("SettingsButton")

        self.wiki_btn = QPushButton(T(self.lang, "Wiki"))
        self.wiki_btn.setObjectName("LinkButton")

        self.tutorial_btn = QPushButton(T(self.lang, "Tutorial"))
        self.tutorial_btn.setObjectName("LinkButton")

        self.credits_btn = QPushButton(T(self.lang, "Credits"))
        self.credits_btn.setObjectName("LinkButton")

        for button in (self.settings_btn, self.wiki_btn, self.tutorial_btn, self.credits_btn):
            button.setFlat(True)
            nav_row.addWidget(button)

        top_row.addLayout(nav_row, 0)
        layout.addLayout(top_row)

        self.hero_subtitle_label = QLabel(T(self.lang, "WorkspaceTagline"))
        self.hero_subtitle_label.setObjectName("HeroSubtitle")
        self.hero_subtitle_label.setWordWrap(True)
        layout.addWidget(self.hero_subtitle_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        layout.addWidget(divider)

        return container

    def _build_configuration_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("ConfigurationPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.cfg_group = QGroupBox()
        self.cfg_group.setObjectName("ConfigCard")
        cfg_layout = QVBoxLayout(self.cfg_group)
        cfg_layout.setSpacing(16)

        self.config_title_label = QLabel(T(self.lang, "SampleSetup"))
        self.config_title_label.setObjectName("CardTitle")
        cfg_layout.addWidget(self.config_title_label)

        self.config_subtitle_label = QLabel(T(self.lang, "SampleSetupDescription"))
        self.config_subtitle_label.setObjectName("CardSubtitle")
        self.config_subtitle_label.setWordWrap(True)
        cfg_layout.addWidget(self.config_subtitle_label)

        self.path_edit = QLineEdit()
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.setPlaceholderText(
            T(self.lang, "Select a folder containing 1.wav, 2.wav, ...")
        )

        self.browse_btn = QPushButton(T(self.lang, "Browse…"))

        self.warn_label = QLabel("")
        self.warn_label.setObjectName("WarnLabel")
        self.warn_label.setVisible(False)
        self.warn_label.setWordWrap(True)

        self.sample_folder_label = QLabel(T(self.lang, "Sample folder"))
        self.sample_folder_label.setObjectName("SectionLabel")

        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)
        folder_row.addWidget(self.path_edit, 1)
        folder_row.addWidget(self.browse_btn, 0)

        cfg_layout.addWidget(self.sample_folder_label)
        cfg_layout.addLayout(folder_row)
        cfg_layout.addWidget(self.warn_label)

        self.timing_section_label = QLabel(T(self.lang, "TimingAndTuning"))
        self.timing_section_label.setObjectName("SectionLabel")
        cfg_layout.addWidget(self.timing_section_label)

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

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.starting_note_label = QLabel(T(self.lang, "Starting note"))
        form.addRow(self.starting_note_label, self.note_combo)

        self.starting_octave_label = QLabel(T(self.lang, "Starting octave"))
        form.addRow(self.starting_octave_label, self.octave_combo)

        self.semitone_range_label = QLabel(T(self.lang, "Semitone range"))
        form.addRow(self.semitone_range_label, self.range_spin)

        self.gap_label = QLabel(T(self.lang, "Gap (seconds)"))
        form.addRow(self.gap_label, self.gap_spin)

        cfg_layout.addLayout(form)

        self.processing_section_label = QLabel(T(self.lang, "ProcessingOptions"))
        self.processing_section_label.setObjectName("SectionLabel")
        cfg_layout.addWidget(self.processing_section_label)

        toggles = QVBoxLayout()
        toggles.setSpacing(6)

        self.opt_pitched = QCheckBox(T(self.lang, "Apply pitch transformation"))
        self.opt_pitched.setChecked(True)
        toggles.addWidget(self.opt_pitched)

        self.opt_dump = QCheckBox(T(self.lang, "Dump individual pitched samples"))
        toggles.addWidget(self.opt_dump)

        self.opt_random = QCheckBox(T(self.lang, "Randomize sample selection"))
        toggles.addWidget(self.opt_random)

        self.opt_normalize = QCheckBox(
            T(self.lang, "Peak normalize each sample (pre-pitch)")
        )
        toggles.addWidget(self.opt_normalize)

        self.opt_slicex_markers = QCheckBox(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )
        toggles.addWidget(self.opt_slicex_markers)

        cfg_layout.addLayout(toggles)
        cfg_layout.addStretch(1)

        layout.addWidget(self.cfg_group)

        return panel

    def _build_generation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("GenerationPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.run_group = QGroupBox()
        self.run_group.setObjectName("RunCard")
        run_layout = QVBoxLayout(self.run_group)
        run_layout.setSpacing(16)

        self.status_title_label = QLabel(T(self.lang, "GenerationStatus"))
        self.status_title_label.setObjectName("CardTitle")
        run_layout.addWidget(self.status_title_label)

        self.summary_label = QLabel(T(self.lang, "SummaryWaiting"))
        self.summary_label.setObjectName("SummaryLabel")
        self.summary_label.setWordWrap(True)
        run_layout.addWidget(self.summary_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        run_layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(T(self.lang, "Logs will appear here…"))
        run_layout.addWidget(self.log, 1)

        self.generate_btn = QPushButton(T(self.lang, "Generate Chromatic"))
        self.generate_btn.setEnabled(False)

        self.cancel_btn = QPushButton(T(self.lang, "Cancel"))
        self.cancel_btn.setEnabled(False)

        primary_actions = QHBoxLayout()
        primary_actions.setSpacing(12)
        primary_actions.addStretch(1)
        primary_actions.addWidget(self.cancel_btn)
        primary_actions.addWidget(self.generate_btn)
        run_layout.addLayout(primary_actions)

        self.open_out_btn = QPushButton(T(self.lang, "Open Output Folder"))
        self.open_out_btn.setEnabled(False)

        secondary_actions = QHBoxLayout()
        secondary_actions.setSpacing(12)
        secondary_actions.addStretch(1)
        secondary_actions.addWidget(self.open_out_btn)
        run_layout.addLayout(secondary_actions)

        layout.addWidget(self.run_group, 1)

        return panel

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("FooterFrame")

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.footer_label = QLabel(T(self.lang, "Footer"))
        self.footer_label.setObjectName("Footer")
        self.footer_label.setWordWrap(True)
        layout.addWidget(self.footer_label)

        return footer

    def _connect_signals(self) -> None:
        self.browse_btn.clicked.connect(self.choose_folder)
        self.path_edit.textChanged.connect(self.refresh_validation)

        self.range_spin.valueChanged.connect(self._on_numeric_changed)
        self.gap_spin.valueChanged.connect(self._on_numeric_changed)
        self.note_combo.currentIndexChanged.connect(self._on_selection_changed)
        self.octave_combo.currentIndexChanged.connect(self._on_selection_changed)

        self.generate_btn.clicked.connect(self.start_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.open_out_btn.clicked.connect(self.open_output_folder_clicked)

        self.settings_btn.clicked.connect(self.show_settings)
        self.wiki_btn.clicked.connect(self.open_wiki)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        self.credits_btn.clicked.connect(self.show_credits)

    def _on_numeric_changed(self, *_: object) -> None:
        self.refresh_button_state()
        self.update_summary()

    def _on_selection_changed(self, *_: object) -> None:
        self.update_summary()

    def apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.mode, self.accent))

    def build_menus(self) -> None:
        bar = self.menuBar()
        bar.clear()

        file_menu = bar.addMenu(T(self.lang, "&File"))

        act_open_folder = QAction(T(self.lang, "Open Sample Folder…"), self)
        act_open_folder.triggered.connect(self.choose_folder)
        file_menu.addAction(act_open_folder)

        reveal_output = QAction(T(self.lang, "Open Output Folder"), self)
        reveal_output.triggered.connect(self.open_output_folder_clicked)
        file_menu.addAction(reveal_output)

        file_menu.addSeparator()

        settings_action = QAction(T(self.lang, "Settings"), self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        help_menu = bar.addMenu(T(self.lang, "&Help"))
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

    def retranslate_all(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.hero_title_label.setText(T(self.lang, "WorkspaceHeadline"))
        self.hero_title_label.setAccessibleDescription(
            T(self.lang, "WorkspaceHeadline")
        )
        self.hero_subtitle_label.setText(T(self.lang, "WorkspaceTagline"))

        self.cfg_group.setTitle(T(self.lang, "Configuration"))
        self.config_title_label.setText(T(self.lang, "SampleSetup"))
        self.config_subtitle_label.setText(T(self.lang, "SampleSetupDescription"))
        self.sample_folder_label.setText(T(self.lang, "Sample folder"))
        self.timing_section_label.setText(T(self.lang, "TimingAndTuning"))
        self.starting_note_label.setText(T(self.lang, "Starting note"))
        self.starting_octave_label.setText(T(self.lang, "Starting octave"))
        self.semitone_range_label.setText(T(self.lang, "Semitone range"))
        self.gap_label.setText(T(self.lang, "Gap (seconds)"))
        self.processing_section_label.setText(T(self.lang, "ProcessingOptions"))
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
        self.settings_btn.setText(T(self.lang, "Settings"))
        self.wiki_btn.setText(T(self.lang, "Wiki"))
        self.tutorial_btn.setText(T(self.lang, "Tutorial"))
        self.credits_btn.setText(T(self.lang, "Credits"))
        self.status_title_label.setText(T(self.lang, "GenerationStatus"))
        self.generate_btn.setText(T(self.lang, "Generate Chromatic"))
        self.cancel_btn.setText(T(self.lang, "Cancel"))
        self.open_out_btn.setText(T(self.lang, "Open Output Folder"))
        self.footer_label.setText(T(self.lang, "Footer"))

        self.path_edit.setAccessibleName(T(self.lang, "Sample folder"))
        self.note_combo.setAccessibleName(T(self.lang, "Starting note"))
        self.octave_combo.setAccessibleName(T(self.lang, "Starting octave"))
        self.range_spin.setAccessibleName(T(self.lang, "Semitone range"))
        self.gap_spin.setAccessibleName(T(self.lang, "Gap (seconds)"))

        self.build_menus()

        self.refresh_validation()
        self.update_summary()

    def show_settings(self) -> None:
        dialog = SettingsDialog(
            lang=self.lang,
            mode=self.mode,
            accent=self.accent,
            languages=list(list_languages()),
            parent=self,
        )
        if dialog.exec():
            new_mode, new_accent, new_lang = dialog.selected_values()
            if new_mode != self.mode or new_accent != self.accent:
                self.mode = new_mode
                self.accent = new_accent
                self.apply_theme()
            if new_lang and new_lang != self.lang:
                self.lang = new_lang
                self.retranslate_all()

    def update_summary(self) -> None:
        if not hasattr(self, "summary_label"):
            return

        if self.folder_valid():
            note = self.note_combo.currentText()
            octave = self.octave_combo.currentText()
            semitones = self.range_spin.value()
            gap = self.gap_spin.value()
            summary = T(
                self.lang,
                "SummaryReady",
                note=note,
                octave=octave,
                semitones=semitones,
                gap=gap,
            )
            self._set_summary_state("ready")
        else:
            summary = T(self.lang, "SummaryWaiting")
            self._set_summary_state("idle")

        self.summary_label.setText(summary)

    def _set_summary_state(self, state: str) -> None:
        self.summary_label.setProperty("state", state)
        self.summary_label.style().unpolish(self.summary_label)
        self.summary_label.style().polish(self.summary_label)

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
        self.update_summary()

    def refresh_button_state(self) -> None:
        ok = (
            self.folder_valid()
            and self.range_spin.value() > 0
            and (0.0 <= self.gap_spin.value() <= MAX_GAP_SEC)
        )
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
        randomize = self.opt_random.isChecked()
        normalize = self.opt_normalize.isChecked()
        slicex_markers = self.opt_slicex_markers.isChecked()
        start_note_index = self.note_combo.currentIndex()
        start_octave = int(self.octave_combo.currentText())

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
