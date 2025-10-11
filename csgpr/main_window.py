from __future__ import annotations

"""Primary Qt window for the Chromatic Scale Generator PLUS!"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QDesktopServices,
    QFontDatabase,
    QIcon,
    QKeySequence,
    QTextCursor,
    QTextOption,
    QShortcut,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
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
from .dialogs import CreditsDialog, SettingsDialog, SettingsState
from .generation import GenerateWorker
from .styles import DEFAULT_ACCENT, build_stylesheet


class PathDisplayField(QLineEdit):
    """Read-only line edit that elides the middle of long paths."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = ""
        self._show_full_text = False
        self.setReadOnly(True)
        self.setCursorPosition(0)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

    def set_path(self, path: str) -> None:
        self._full_text = path
        self.setToolTip(path if path else "")
        self._update_display()

    def clear_path(self) -> None:
        self._full_text = ""
        self.setToolTip("")
        self._update_display()

    def current_path(self) -> str:
        return self._full_text

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if not self._show_full_text:
            self._update_display()

    def focusInEvent(self, event) -> None:  # type: ignore[override]
        self._show_full_text = True
        super().setText(self._full_text)
        super().focusInEvent(event)
        self.selectAll()

    def focusOutEvent(self, event) -> None:  # type: ignore[override]
        self._show_full_text = False
        super().focusOutEvent(event)
        self._update_display()

    def _update_display(self) -> None:
        if not self._full_text:
            super().setText("")
            return
        if self._show_full_text:
            super().setText(self._full_text)
            return
        metrics = self.fontMetrics()
        contents = self.contentsMargins()
        available = max(0, self.width() - (contents.left() + contents.right()) - 12)
        elided = metrics.elidedText(self._full_text, Qt.ElideMiddle, available)
        super().setText(elided)


class MainWindow(QMainWindow):
    """Main application shell."""

    def __init__(self) -> None:
        super().__init__()
        self.lang = "en"
        self.accent = DEFAULT_ACCENT
        self.auto_reload_translations = False
        self.verbose_logging = False
        self.output_directory: Optional[Path] = None

        self.worker: Optional[GenerateWorker] = None
        self.last_output_path: Optional[Path] = None

        self._init_window()
        self._build_ui()
        self._connect_signals()
        self._configure_shortcuts()
        self._configure_tab_order()
        self.apply_theme()

        self.setAcceptDrops(True)
        self.refresh_validation()
        self.update_summary()
        self.refresh_button_state()

    def _init_window(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 820)
        self.setMinimumSize(880, 620)
        if os.path.exists(APP_ICON_PATH):
            try:
                self.setWindowIcon(QIcon(APP_ICON_PATH))
            except Exception:  # pragma: no cover - environment specific
                pass

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        outer.addWidget(self._build_header())

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setObjectName("ContentSplitter")

        self.main_splitter.addWidget(self._build_sample_panel())
        self.main_splitter.addWidget(self._build_status_panel())
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 4)

        outer.addWidget(self.main_splitter, 1)
        outer.addWidget(self._build_footer())

        self.setStatusBar(QStatusBar())
        self.reset_layout()

    def _build_header(self) -> QWidget:
        container = QFrame()
        container.setObjectName("HeaderBar")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.header_title = QLabel(APP_TITLE)
        self.header_title.setObjectName("HeaderTitle")
        self.header_title.setAccessibleName(APP_TITLE)
        layout.addWidget(self.header_title, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.settings_btn = QPushButton(T(self.lang, "Settings"))
        self.settings_btn.setObjectName("QuickActionAccent")

        self.wiki_btn = QPushButton(T(self.lang, "Wiki"))
        self.wiki_btn.setObjectName("QuickActionLink")

        self.tutorial_btn = QPushButton(T(self.lang, "Tutorial"))
        self.tutorial_btn.setObjectName("QuickActionLink")

        self.credits_btn = QPushButton(T(self.lang, "Credits"))
        self.credits_btn.setObjectName("QuickActionLink")

        for button in (
            self.settings_btn,
            self.wiki_btn,
            self.tutorial_btn,
            self.credits_btn,
        ):
            button.setCursor(Qt.PointingHandCursor)
            actions.addWidget(button)

        layout.addLayout(actions)
        return container

    def _build_sample_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)

        title = QLabel(T(self.lang, "SampleSetup"))
        title.setObjectName("CardTitle")
        card_layout.addWidget(title)

        self.sample_intro = QLabel(T(self.lang, "SampleSetupIntro"))
        self.sample_intro.setObjectName("CardSubtitle")
        self.sample_intro.setWordWrap(True)
        card_layout.addWidget(self.sample_intro)

        self.sample_folder_label = QLabel(T(self.lang, "Sample folder"))
        self.sample_folder_label.setObjectName("SectionHeader")
        card_layout.addWidget(self.sample_folder_label)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)
        self.sample_path_display = PathDisplayField()
        self.sample_path_display.setPlaceholderText(
            T(self.lang, "Select a folder containing 1.wav, 2.wav, ...")
        )
        self.sample_path_display.setAccessibleName(T(self.lang, "Sample folder"))
        folder_row.addWidget(self.sample_path_display, 1)

        self.browse_btn = QPushButton(T(self.lang, "Browse…"))
        self.browse_btn.setObjectName("PrimaryAction")
        folder_row.addWidget(self.browse_btn, 0)
        card_layout.addLayout(folder_row)

        self.validation_label = QLabel("")
        self.validation_label.setObjectName("ValidationLabel")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        card_layout.addWidget(self.validation_label)

        self.timing_label = QLabel(T(self.lang, "TimingAndTuning"))
        self.timing_label.setObjectName("SectionHeader")
        card_layout.addWidget(self.timing_label)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.note_combo = QComboBox()
        self.note_combo.addItems(NOTE_NAMES)
        self.note_combo.setCurrentIndex(0)
        self.note_combo.setToolTip(T(self.lang, "StartingNoteHint"))
        self.note_combo.setAccessibleName(T(self.lang, "Starting note"))
        form.addRow(T(self.lang, "Starting note"), self.note_combo)

        self.octave_combo = QComboBox()
        for octave in OCTAVES:
            self.octave_combo.addItem(str(octave))
        self.octave_combo.setCurrentText("3")
        self.octave_combo.setToolTip(T(self.lang, "StartingOctaveHint"))
        self.octave_combo.setAccessibleName(T(self.lang, "Starting octave"))
        form.addRow(T(self.lang, "Starting octave"), self.octave_combo)

        self.range_spin = QSpinBox()
        self.range_spin.setRange(1, MAX_SEMITONES)
        self.range_spin.setValue(36)
        self.range_spin.setToolTip(T(self.lang, "SemitoneRangeHint"))
        self.range_spin.setAccessibleName(T(self.lang, "Semitone range"))
        form.addRow(T(self.lang, "Semitone range"), self.range_spin)

        self.gap_spin = QDoubleSpinBox()
        self.gap_spin.setRange(0.0, MAX_GAP_SEC)
        self.gap_spin.setDecimals(3)
        self.gap_spin.setSingleStep(0.05)
        self.gap_spin.setValue(0.30)
        self.gap_spin.setToolTip(T(self.lang, "GapSecondsHint"))
        self.gap_spin.setAccessibleName(T(self.lang, "Gap (seconds)"))
        form.addRow(T(self.lang, "Gap (seconds)"), self.gap_spin)

        card_layout.addLayout(form)

        self.processing_label = QLabel(T(self.lang, "ProcessingOptions"))
        self.processing_label.setObjectName("SectionHeader")
        card_layout.addWidget(self.processing_label)

        toggles = QVBoxLayout()
        toggles.setSpacing(10)

        self.opt_pitched = QCheckBox(T(self.lang, "Apply pitch transformation"))
        self.opt_pitched.setChecked(True)
        self.opt_pitched.setWordWrap(True)
        self.opt_pitched.setAccessibleName(T(self.lang, "Apply pitch transformation"))
        toggles.addWidget(self.opt_pitched)

        self.opt_dump = QCheckBox(T(self.lang, "Dump individual pitched samples"))
        self.opt_dump.setWordWrap(True)
        self.opt_dump.setAccessibleName(T(self.lang, "Dump individual pitched samples"))
        toggles.addWidget(self.opt_dump)

        self.opt_random = QCheckBox(T(self.lang, "Randomize sample selection"))
        self.opt_random.setWordWrap(True)
        self.opt_random.setAccessibleName(T(self.lang, "Randomize sample selection"))
        toggles.addWidget(self.opt_random)

        self.opt_normalize = QCheckBox(T(self.lang, "Peak normalize each sample (pre-pitch)"))
        self.opt_normalize.setWordWrap(True)
        self.opt_normalize.setAccessibleName(
            T(self.lang, "Peak normalize each sample (pre-pitch)")
        )
        toggles.addWidget(self.opt_normalize)

        self.opt_slicex_markers = QCheckBox(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )
        self.opt_slicex_markers.setWordWrap(True)
        self.opt_slicex_markers.setAccessibleName(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )
        toggles.addWidget(self.opt_slicex_markers)

        card_layout.addLayout(toggles)
        card_layout.addStretch(1)
        layout.addWidget(card)
        layout.addStretch(1)
        return container

    def _build_status_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card = QFrame()
        card.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)

        title = QLabel(T(self.lang, "GenerationStatus"))
        title.setObjectName("CardTitle")
        card_layout.addWidget(title)

        self.summary_label = QLabel(T(self.lang, "SummaryWaiting"))
        self.summary_label.setObjectName("MutedLabel")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAccessibleName(T(self.lang, "GenerationSummary"))
        card_layout.addWidget(self.summary_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setAccessibleName(T(self.lang, "GenerationProgress"))
        card_layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(T(self.lang, "Logs will appear here…"))
        self.log.setWordWrapMode(QTextOption.NoWrap)
        self.log.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.log.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.log.setFont(fixed_font)
        self.log.setAccessibleName(T(self.lang, "LogOutput"))
        card_layout.addWidget(self.log, 1)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addStretch(1)

        self.open_out_btn = QPushButton(T(self.lang, "Open Output Folder"))
        self.open_out_btn.setObjectName("TertiaryAction")
        self.open_out_btn.setEnabled(False)
        self.open_out_btn.setAccessibleName(T(self.lang, "Open Output Folder"))
        actions.addWidget(self.open_out_btn)

        self.cancel_btn = QPushButton(T(self.lang, "Cancel"))
        self.cancel_btn.setObjectName("SecondaryAction")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setAccessibleName(T(self.lang, "Cancel"))
        actions.addWidget(self.cancel_btn)

        self.generate_btn = QPushButton(T(self.lang, "Generate Chromatic"))
        self.generate_btn.setObjectName("PrimaryAction")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setAccessibleName(T(self.lang, "Generate Chromatic"))
        actions.addWidget(self.generate_btn)

        card_layout.addLayout(actions)
        layout.addWidget(card)
        layout.addStretch(1)
        return container

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("FooterBar")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.footer_label = QLabel(T(self.lang, "Footer"))
        self.footer_label.setObjectName("FooterLabel")
        self.footer_label.setWordWrap(True)
        layout.addWidget(self.footer_label, 1)

        return footer

    def _connect_signals(self) -> None:
        self.browse_btn.clicked.connect(self.choose_folder)

        self.range_spin.valueChanged.connect(self._on_configuration_changed)
        self.gap_spin.valueChanged.connect(self._on_configuration_changed)
        self.note_combo.currentIndexChanged.connect(self._on_configuration_changed)
        self.octave_combo.currentIndexChanged.connect(self._on_configuration_changed)

        self.opt_pitched.stateChanged.connect(self._on_configuration_changed)
        self.opt_dump.stateChanged.connect(self._on_configuration_changed)
        self.opt_random.stateChanged.connect(self._on_configuration_changed)
        self.opt_normalize.stateChanged.connect(self._on_configuration_changed)
        self.opt_slicex_markers.stateChanged.connect(self._on_configuration_changed)

        self.generate_btn.clicked.connect(self.start_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.open_out_btn.clicked.connect(self.open_output_folder_clicked)

        self.settings_btn.clicked.connect(self.show_settings)
        self.wiki_btn.clicked.connect(self.open_wiki)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        self.credits_btn.clicked.connect(self.show_credits)

    def _configure_shortcuts(self) -> None:
        shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_open.activated.connect(self.choose_folder)

        shortcut_generate = QShortcut(QKeySequence("Ctrl+G"), self)
        shortcut_generate.activated.connect(self.start_generation)

    def apply_theme(self) -> None:
        self.setStyleSheet(build_stylesheet(self.accent))

    def retranslate_all(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.header_title.setText(APP_TITLE)
        self.settings_btn.setText(T(self.lang, "Settings"))
        self.wiki_btn.setText(T(self.lang, "Wiki"))
        self.tutorial_btn.setText(T(self.lang, "Tutorial"))
        self.credits_btn.setText(T(self.lang, "Credits"))

        self.sample_intro.setText(T(self.lang, "SampleSetupIntro"))
        self.sample_folder_label.setText(T(self.lang, "Sample folder"))
        self.sample_path_display.setPlaceholderText(
            T(self.lang, "Select a folder containing 1.wav, 2.wav, ...")
        )
        self.sample_path_display.setAccessibleName(T(self.lang, "Sample folder"))
        self.browse_btn.setText(T(self.lang, "Browse…"))
        self.timing_label.setText(T(self.lang, "TimingAndTuning"))
        self.processing_label.setText(T(self.lang, "ProcessingOptions"))
        self.note_combo.setToolTip(T(self.lang, "StartingNoteHint"))
        self.octave_combo.setToolTip(T(self.lang, "StartingOctaveHint"))
        self.range_spin.setToolTip(T(self.lang, "SemitoneRangeHint"))
        self.gap_spin.setToolTip(T(self.lang, "GapSecondsHint"))
        self.note_combo.setAccessibleName(T(self.lang, "Starting note"))
        self.octave_combo.setAccessibleName(T(self.lang, "Starting octave"))
        self.range_spin.setAccessibleName(T(self.lang, "Semitone range"))
        self.gap_spin.setAccessibleName(T(self.lang, "Gap (seconds)"))
        self.opt_pitched.setText(T(self.lang, "Apply pitch transformation"))
        self.opt_dump.setText(T(self.lang, "Dump individual pitched samples"))
        self.opt_random.setText(T(self.lang, "Randomize sample selection"))
        self.opt_normalize.setText(T(self.lang, "Peak normalize each sample (pre-pitch)"))
        self.opt_slicex_markers.setText(T(self.lang, "Embed FL Studio Slicex slice markers"))
        self.opt_pitched.setAccessibleName(T(self.lang, "Apply pitch transformation"))
        self.opt_dump.setAccessibleName(T(self.lang, "Dump individual pitched samples"))
        self.opt_random.setAccessibleName(T(self.lang, "Randomize sample selection"))
        self.opt_normalize.setAccessibleName(T(self.lang, "Peak normalize each sample (pre-pitch)"))
        self.opt_slicex_markers.setAccessibleName(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )

        self.summary_label.setText(T(self.lang, "SummaryWaiting"))
        self.summary_label.setAccessibleName(T(self.lang, "GenerationSummary"))
        self.progress.setAccessibleName(T(self.lang, "GenerationProgress"))
        self.log.setPlaceholderText(T(self.lang, "Logs will appear here…"))
        self.log.setAccessibleName(T(self.lang, "LogOutput"))
        self.generate_btn.setText(T(self.lang, "Generate Chromatic"))
        self.generate_btn.setAccessibleName(T(self.lang, "Generate Chromatic"))
        self.cancel_btn.setText(T(self.lang, "Cancel"))
        self.cancel_btn.setAccessibleName(T(self.lang, "Cancel"))
        self.open_out_btn.setText(T(self.lang, "Open Output Folder"))
        self.open_out_btn.setAccessibleName(T(self.lang, "Open Output Folder"))
        self.footer_label.setText(T(self.lang, "Footer"))

        self.refresh_validation()
        self.update_summary()

    def show_settings(self) -> None:
        state = SettingsState(
            language=self.lang,
            auto_reload=self.auto_reload_translations,
            output_path=str(self.output_directory or ""),
            verbose_logging=self.verbose_logging,
        )
        dialog = SettingsDialog(
            lang=self.lang,
            languages=list(list_languages()),
            state=state,
            parent=self,
        )
        if dialog.exec():
            result = dialog.selected_values()
            if result.language != self.lang:
                self.lang = result.language
                self.retranslate_all()
            self.auto_reload_translations = result.auto_reload
            self.verbose_logging = result.verbose_logging
            self.output_directory = Path(result.output_path) if result.output_path else None
            if result.reset_layout:
                self.reset_layout()
                self.statusBar().showMessage(T(self.lang, "LayoutResetMessage"), 5000)

    def update_summary(self) -> None:
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
        else:
            summary = T(self.lang, "SummaryWaiting")
        self.summary_label.setText(summary)

    def _on_configuration_changed(self, *_: object) -> None:
        self.refresh_button_state()
        self.update_summary()

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if os.path.isdir(path):
            self.sample_path_display.set_path(path)
            self.refresh_validation()

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
        path = Path(self.sample_path_display.current_path())
        return path.exists() and path.is_dir() and (path / "1.wav").exists()

    def refresh_validation(self) -> None:
        text = self.sample_path_display.current_path().strip()
        if not text:
            self.validation_label.setVisible(False)
        else:
            path = Path(text)
            if not path.exists() or not path.is_dir():
                self.validation_label.setText(T(self.lang, "Folder not found."))
                self.validation_label.setVisible(True)
            elif not (path / "1.wav").exists():
                self.validation_label.setText(
                    T(self.lang, "Need at least 1.wav in this folder.")
                )
                self.validation_label.setVisible(True)
            else:
                idx = 1
                while (path / f"{idx}.wav").exists():
                    idx += 1
                if idx == 1:
                    self.validation_label.setText(
                        T(self.lang, "No sequential samples found (1.wav, 2.wav, ...).")
                    )
                    self.validation_label.setVisible(True)
                else:
                    self.validation_label.setVisible(False)
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
            self.last_output_path is not None and os.path.exists(self.last_output_path)
        )

    def choose_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, T(self.lang, "Select Sample Folder"), os.path.expanduser("~")
        )
        if path:
            self.sample_path_display.set_path(path)
            self.statusBar().showMessage(T(self.lang, "Selected folder: {p}", p=path), 5000)
            self.refresh_validation()

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

    def start_generation(self) -> None:
        if not self.folder_valid():
            self.show_error(T(self.lang, "Invalid folder. Place '1.wav', '2.wav', ... in it."))
            return

        sample_path = Path(self.sample_path_display.current_path().strip())
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

    def cancel_generation(self) -> None:
        if self.worker:
            self.worker.request_cancel()
            self.statusBar().showMessage(T(self.lang, "Cancelling…"))

    def append_log(self, text: str) -> None:
        self.log.appendPlainText(text)
        self.log.moveCursor(QTextCursor.End)

    def on_worker_finished(self) -> None:
        self.worker = None
        self.refresh_button_state()

    def on_done(self, out_path: str) -> None:
        self.statusBar().showMessage(T(self.lang, "Done! Saved to {p}", p=out_path), 8000)
        self.append_log(T(self.lang, "✅ Completed! Output: {p}", p=out_path))
        self.progress.setValue(100)
        self.last_output_path = Path(out_path)
        self.open_out_btn.setEnabled(True)

    def on_error(self, msg: str) -> None:
        self.statusBar().showMessage(T(self.lang, "An error occurred."), 8000)
        self.append_log(T(self.lang, "❌ Error: {m}", m=msg))
        self.show_error(msg)

    def on_cancelled(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 8000)
        self.append_log(T(self.lang, "⚠️ Generation was cancelled."))
        self.progress.setValue(0)

    def _configure_tab_order(self) -> None:
        order = [
            self.settings_btn,
            self.wiki_btn,
            self.tutorial_btn,
            self.credits_btn,
            self.browse_btn,
            self.note_combo,
            self.octave_combo,
            self.range_spin,
            self.gap_spin,
            self.opt_pitched,
            self.opt_dump,
            self.opt_random,
            self.opt_normalize,
            self.opt_slicex_markers,
            self.generate_btn,
            self.cancel_btn,
            self.open_out_btn,
        ]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)

    def reset_layout(self) -> None:
        self.main_splitter.setSizes([3, 4])


__all__ = ["MainWindow"]
