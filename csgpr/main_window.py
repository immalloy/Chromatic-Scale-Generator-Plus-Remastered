from __future__ import annotations

"""Primary Qt window for the Chromatic Scale Generator PLUS!"""

import os
import subprocess
from pathlib import Path

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T

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

        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1040, 680)

        try:
            if os.path.exists(APP_ICON_PATH):
                self.setWindowIcon(QIcon(APP_ICON_PATH))
        except Exception:  # pragma: no cover - environment specific
            pass

        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 16)
        outer.setSpacing(20)

        self.cfg_group = QGroupBox(T(self.lang, "Configuration"))
        cfg_layout = QGridLayout(self.cfg_group)
        cfg_layout.setContentsMargins(16, 20, 16, 16)
        cfg_layout.setHorizontalSpacing(12)
        cfg_layout.setVerticalSpacing(10)
        cfg_layout.setColumnStretch(0, 0)
        cfg_layout.setColumnStretch(1, 1)

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

        row = 0
        self.sample_folder_label = QLabel(T(self.lang, "Sample folder"))
        cfg_layout.addWidget(self.sample_folder_label, row, 0)
        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        folder_row.addWidget(self.path_edit, 1)
        folder_row.addWidget(self.browse_btn, 0)
        cfg_layout.addLayout(folder_row, row, 1)
        row += 1

        cfg_layout.addWidget(self.warn_label, row, 0, 1, 2)
        row += 1

        self.starting_note_label = QLabel(T(self.lang, "Starting note"))
        cfg_layout.addWidget(self.starting_note_label, row, 0)
        cfg_layout.addWidget(self.note_combo, row, 1)
        row += 1

        self.starting_octave_label = QLabel(T(self.lang, "Starting octave"))
        cfg_layout.addWidget(self.starting_octave_label, row, 0)
        cfg_layout.addWidget(self.octave_combo, row, 1)
        row += 1

        self.semitone_range_label = QLabel(T(self.lang, "Semitone range"))
        cfg_layout.addWidget(self.semitone_range_label, row, 0)
        cfg_layout.addWidget(self.range_spin, row, 1)
        row += 1

        self.gap_label = QLabel(T(self.lang, "Gap (seconds)"))
        cfg_layout.addWidget(self.gap_label, row, 0)
        cfg_layout.addWidget(self.gap_spin, row, 1)

        self.advanced_group = QGroupBox(T(self.lang, "Advanced Options"))
        advanced_layout = QVBoxLayout(self.advanced_group)
        advanced_layout.setContentsMargins(16, 20, 16, 16)
        advanced_layout.setSpacing(8)

        self.opt_pitched = QCheckBox(T(self.lang, "Apply pitch transformation"))
        self.opt_pitched.setChecked(True)
        self.opt_dump = QCheckBox(T(self.lang, "Dump individual pitched samples"))
        self.opt_random = QCheckBox(T(self.lang, "Randomize sample selection"))
        self.opt_normalize = QCheckBox(
            T(self.lang, "Peak normalize each sample (pre-pitch)")
        )
        self.opt_slicex_markers = QCheckBox(
            T(self.lang, "Embed FL Studio Slicex slice markers")
        )

        for widget in (
            self.opt_pitched,
            self.opt_dump,
            self.opt_random,
            self.opt_normalize,
            self.opt_slicex_markers,
        ):
            advanced_layout.addWidget(widget)

        advanced_layout.addStretch(1)

        self.run_group = QGroupBox(T(self.lang, "Run"))
        run_layout = QVBoxLayout(self.run_group)
        run_layout.setContentsMargins(16, 20, 16, 16)
        run_layout.setSpacing(12)

        btns_row = QHBoxLayout()
        btns_row.setSpacing(10)
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

        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.addWidget(self.cfg_group, 2)
        top_row.addWidget(self.advanced_group, 1)
        outer.addLayout(top_row, 0)
        outer.addWidget(self.run_group, 1)

        footer_row = QHBoxLayout()
        footer_row.setSpacing(12)
        self.footer = QLabel(T(self.lang, "Footer"))
        self.footer.setWordWrap(True)
        self.footer.setObjectName("Footer")
        self.wiki_btn = QPushButton(T(self.lang, "Wiki"))
        self.wiki_btn.setObjectName("LinkButton")
        self.tutorial_btn = QPushButton(T(self.lang, "Tutorial"))
        self.tutorial_btn.setObjectName("LinkButton")
        self.credits_btn = QPushButton(T(self.lang, "Credits"))
        self.credits_btn.setObjectName("LinkButton")
        self.settings_footer_btn = QPushButton(T(self.lang, "Settings"))
        self.settings_footer_btn.setObjectName("LinkButton")
        footer_row.addWidget(self.footer, 1)
        footer_row.addStretch(1)
        footer_row.addWidget(self.wiki_btn, 0)
        footer_row.addWidget(self.tutorial_btn, 0)
        footer_row.addWidget(self.credits_btn, 0)
        footer_row.addWidget(self.settings_footer_btn, 0)
        outer.addLayout(footer_row)

        self.setStatusBar(QStatusBar())
        self.apply_theme()
        self.build_menus()

        self.path_edit.textChanged.connect(self.refresh_validation)
        self.generate_btn.clicked.connect(self.start_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.open_out_btn.clicked.connect(self.open_output_folder_clicked)
        self.wiki_btn.clicked.connect(self.open_wiki)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        self.credits_btn.clicked.connect(self.show_credits)
        self.settings_footer_btn.clicked.connect(self.open_settings_dialog)

        self.worker: GenerateWorker | None = None
        self.last_output_path: Path | None = None

        self.setAcceptDrops(True)
        self.refresh_validation()
        self.refresh_button_state()

    def apply_theme(self) -> None:
        stylesheet = build_stylesheet(self.mode, self.accent)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet)
        self.setStyleSheet(stylesheet)

    def build_menus(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.clear()

        settings_menu = menu_bar.addMenu(T(self.lang, "&Settings"))
        settings_action = QAction(T(self.lang, "Open Settings…"), self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu(T(self.lang, "&Help"))
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
        self.cfg_group.setTitle(T(self.lang, "Configuration"))
        self.advanced_group.setTitle(T(self.lang, "Advanced Options"))
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
        self.generate_btn.setText(T(self.lang, "Generate Chromatic"))
        self.cancel_btn.setText(T(self.lang, "Cancel"))
        self.open_out_btn.setText(T(self.lang, "Open Output Folder"))
        self.wiki_btn.setText(T(self.lang, "Wiki"))
        self.tutorial_btn.setText(T(self.lang, "Tutorial"))
        self.credits_btn.setText(T(self.lang, "Credits"))
        self.settings_footer_btn.setText(T(self.lang, "Settings"))
        self.footer.setText(T(self.lang, "Footer"))

        self.build_menus()

        self.refresh_validation()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.lang, self.mode, self.accent, self)
        if dialog.exec():
            mode, accent, lang = dialog.values()
            if mode != self.mode or accent != self.accent:
                self.mode = mode
                self.accent = accent
                self.apply_theme()
            if lang != self.lang:
                self.lang = lang
                self.retranslate_all()

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
