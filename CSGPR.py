# chromatic_gen_qt_plus_modular_i18n.py
# Main app imports i18n_pkg.* (separate files for each language + handler)
from __future__ import annotations
import os, sys, random, subprocess
from pathlib import Path
from typing import List

# Dependency hints
def _require(modname: str, pip_name: str | None = None):
    try:
        __import__(modname)
    except ImportError as e:
        pkg = pip_name or modname
        raise SystemExit(f"Missing dependency: {modname}\nFix with:  pip install {pkg}\n") from e

for _mod, _pip in [("numpy","numpy"), ("PySide6","PySide6"), ("parselmouth","praat-parselmouth")]:
    _require(_mod, _pip)

import numpy as np
import parselmouth

from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl
from PySide6.QtGui import QIcon, QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QFileDialog, QLineEdit, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox,
    QProgressBar, QTextEdit, QStatusBar, QMessageBox, QDialog, QDialogButtonBox
)

# i18n package
from i18n_pkg import T, list_languages

APP_TITLE = "Chromatic Scale Generator PLUS! (REMASTERED)"
APP_ICON_PATH = r"C:\Users\Administrator\Downloads\CSGR\icon.ico"  # optional
DEFAULT_SR = 48000
NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
OCTAVES = [2,3,4,5,6,7]
MAX_SEMITONES = 128
MAX_GAP_SEC = 5.0
DISCORD_INVITE = "https://discord.gg/pe6J4FbcCU"

PALETTES = {
    ("dark", "blue"): dict(bg="#121212", panel="#1A1A1A", text="#EDEDED", sub="#C9C9C9",
                           field="#222222", border="#2F2F2F", accent="#2D7CF3", accent2="#5AA1FF",
                           warn="#FFB3B3", muted="#9A9A9A"),
    ("dark", "pink"): dict(bg="#121212", panel="#1A1A1A", text="#F4F1F6", sub="#D6B2C8",
                           field="#222222", border="#2F2F2F", accent="#FF5AA1", accent2="#FF9AC0",
                           warn="#FFC2D6", muted="#9A9A9A"),
    ("light", "blue"): dict(bg="#F7F7FA", panel="#FFFFFF", text="#1B1B1B", sub="#5A5A5A",
                            field="#FFFFFF", border="#D7D7DD", accent="#2D7CF3", accent2="#5AA1FF",
                            warn="#B00020", muted="#6F6F77"),
    ("light", "pink"): dict(bg="#FDF7FA", panel="#FFFFFF", text="#1B1B1B", sub="#7B5163",
                            field="#FFFFFF", border="#E6D6DE", accent="#FF5AA1", accent2="#FF7EB9",
                            warn="#B00020", muted="#6F6F77"),
}
def build_stylesheet(mode: str, accent: str) -> str:
    p = PALETTES[(mode, accent)]
    return f"""
        QMainWindow {{ background: {p['bg']}; }}
        QGroupBox {{
            color: {p['text']};
            border: 1px solid {p['border']};
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            background: {p['panel']};
        }}
        QLabel, QCheckBox, QStatusBar, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
            color: {p['text']};
            font-size: 14px;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
            background: {p['field']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 6px;
            color: {p['text']};
        }}
        QPushButton {{
            background: {p['accent']};
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            color: white;
            font-weight: 600;
        }}
        QPushButton:disabled {{ background: {p['border']}; color: {p['muted']}; }}
        QProgressBar {{
            background: {p['field']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            text-align: center;
            color: {p['text']};
            height: 18px;
        }}
        QProgressBar::chunk {{ border-radius: 8px; margin: 1px; background: {p['accent2']}; }}
        #Footer {{ color: {p['sub']}; font-size: 12px; padding: 8px 0; }}
        #WarnLabel {{ color: {p['warn']}; font-size: 12px; }}
        #LinkButton {{ background: transparent; color: {p['accent']}; border: none; text-decoration: underline; padding: 0px; font-weight: 600; }}
    """

class GenerateWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    done = Signal(str)
    error = Signal(str)
    cancelled = Signal(str)
    def __init__(self, sample_path: Path, semitones: int, gap_seconds: float,
                 pitched: bool, dump_samples: bool, randomize: bool,
                 start_note_index: int, start_octave: int, normalize: bool,
                 lang: str, parent=None):
        super().__init__(parent)
        self.sample_path = sample_path
        self.semitones = semitones
        self.gap_seconds = gap_seconds
        self.pitched = pitched
        self.dump_samples = dump_samples
        self.randomize = randomize
        self.start_note_index = start_note_index
        self.start_octave = start_octave
        self.normalize = normalize
        self.lang = lang
        self._cancel = False
    def request_cancel(self): self._cancel = True
    def _emit(self, text: str): self.log.emit(text)
    def run(self):
        try:
            if not self.sample_path.exists():
                raise FileNotFoundError(T(self.lang,"Folder not found."))
            file_count = 0
            while (self.sample_path / f"{file_count + 1}.wav").exists():
                file_count += 1
            if file_count == 0:
                raise FileNotFoundError(T(self.lang,"No sequential samples found (1.wav, 2.wav, ...)."))
            self._emit(T(self.lang,"Found {n} sample(s) (1.wav..{m}.wav).", n=file_count, m=file_count))
            self._emit(T(self.lang,"Semitones: {s} | Gap: {g:.3f}s | Pitched: {p}", s=self.semitones, g=self.gap_seconds, p=self.pitched))
            if self.normalize:
                self._emit(T(self.lang,"Peak normalization: ON"))
            gap = parselmouth.praat.call("Create Sound from formula","Gap",1,0,float(self.gap_seconds),DEFAULT_SR,"0")
            pitched_sounds: List[parselmouth.Sound] = []; spaced_sounds: List[parselmouth.Sound] = []
            starting_key = self.start_note_index + 12*(self.start_octave - 2)
            for i in range(self.semitones):
                if self._cancel: self.cancelled.emit(T(self.lang,"Cancelled by user.")); return
                idx = random.randint(1, file_count) if self.randomize else (i % file_count) + 1
                file_path = self.sample_path / f"{idx}.wav"
                self._emit(T(self.lang,"[{a}/{b}] Loading {name}", a=i+1, b=self.semitones, name=file_path.name))
                snd = parselmouth.Sound(str(file_path))
                snd = parselmouth.praat.call(snd,"Resample",DEFAULT_SR,1)
                snd = parselmouth.praat.call(snd,"Convert to mono")
                if self.normalize:
                    import numpy as _np
                    arr = snd.values.copy(); peak = float(_np.max(_np.abs(arr)))
                    if peak > 0: arr = arr/peak; snd.values[:] = arr
                    self._emit("  • " + T(self.lang,"normalized"))
                if self.pitched:
                    manipulation = parselmouth.praat.call(snd,"To Manipulation",0.05,60,600)
                    pitch_tier = parselmouth.praat.call(manipulation,"Extract pitch tier")
                    parselmouth.praat.call(pitch_tier,"Formula",f"32.703 * (2 ^ ({i + starting_key + 12}/12))")
                    parselmouth.praat.call([pitch_tier, manipulation],"Replace pitch tier")
                    resynth = parselmouth.praat.call(manipulation,"Get resynthesis (overlap-add)")
                    pitched_sounds.append(resynth); spaced_sounds.append(resynth)
                else:
                    pitched_sounds.append(snd); spaced_sounds.append(snd)
                spaced_sounds.append(gap)
                pct = int(((i+1)/self.semitones)*90); self.progress.emit(min(99,max(1,pct)))
            if self._cancel: self.cancelled.emit(T(self.lang,"Cancelled by user.")); return
            self._emit(T(self.lang,"Concatenating chromatic scale..."))
            chromatic = parselmouth.Sound.concatenate(spaced_sounds)
            out_path = self.sample_path / "chromatic.wav"; chromatic.save(str(out_path),"WAV")
            self._emit(T(self.lang,"Saved: {path}", path=out_path))
            if self.dump_samples and self.pitched:
                dump_dir = self.sample_path / "pitched_samples"; dump_dir.mkdir(exist_ok=True)
                for idx, s in enumerate(pitched_sounds, start=1):
                    fp = dump_dir / f"pitched_{idx}.wav"; s.save(str(fp),"WAV")
                self._emit(T(self.lang,"Dumped {n} pitched sample(s) to: {dir}", n=len(pitched_sounds), dir=dump_dir))
            self.progress.emit(100); self.done.emit(str(out_path))
        except Exception as e:
            self.error.emit(str(e))

class CreditsDialog(QDialog):
    def __init__(self, lang: str, parent=None):
        super().__init__(parent); self.lang = lang
        self.setWindowTitle(T(self.lang,"Credits")); self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        text = QLabel(T(self.lang,"CreditsText")); text.setWordWrap(True); layout.addWidget(text)
        btns = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang,"Join Discord")); self.discord_btn.setObjectName("LinkButton")
        self.discord_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://discord.gg/pe6J4FbcCU")))
        btns.addWidget(self.discord_btn); btns.addStretch(1); layout.addLayout(btns)
        box = QDialogButtonBox(QDialogButtonBox.Ok); box.accepted.connect(self.accept); layout.addWidget(box)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "en"; self.mode = "dark"; self.accent = "pink"
        self.setWindowTitle(APP_TITLE); self.setMinimumSize(1040, 680)
        try:
            if os.path.exists(APP_ICON_PATH): self.setWindowIcon(QIcon(APP_ICON_PATH))
        except Exception: pass
        central = QWidget(); self.setCentralWidget(central)
        cfg_group = QGroupBox(T(self.lang,"Configuration")); cfg_layout = QGridLayout(cfg_group)
        self.path_edit = QLineEdit(); self.path_edit.setPlaceholderText(T(self.lang,"Select a folder containing 1.wav, 2.wav, ..."))
        self.browse_btn = QPushButton(T(self.lang,"Browse…")); self.browse_btn.clicked.connect(self.choose_folder)
        self.warn_label = QLabel(""); self.warn_label.setObjectName("WarnLabel"); self.warn_label.setVisible(False)
        self.note_combo = QComboBox(); self.note_combo.addItems(NOTE_NAMES); self.note_combo.setCurrentIndex(0)
        self.octave_combo = QComboBox(); [self.octave_combo.addItem(str(o)) for o in OCTAVES]; self.octave_combo.setCurrentText("3")
        self.range_spin = QSpinBox(); self.range_spin.setRange(1, MAX_SEMITONES); self.range_spin.setValue(36)
        self.gap_spin = QDoubleSpinBox(); self.gap_spin.setRange(0.0, MAX_GAP_SEC); self.gap_spin.setDecimals(3); self.gap_spin.setSingleStep(0.05); self.gap_spin.setValue(0.30)
        self.opt_pitched = QCheckBox(T(self.lang,"Apply pitch transformation")); self.opt_pitched.setChecked(True)
        self.opt_dump = QCheckBox(T(self.lang,"Dump individual pitched samples"))
        self.opt_random = QCheckBox(T(self.lang,"Randomize sample selection"))
        self.opt_normalize = QCheckBox(T(self.lang,"Peak normalize each sample (pre-pitch)"))
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["dark","light"]); self.mode_combo.setCurrentText(self.mode)
        self.accent_combo = QComboBox(); self.accent_combo.addItems(["blue","pink"]); self.accent_combo.setCurrentText(self.accent)
        self.lang_combo = QComboBox()
        for code, label in list_languages():
            self.lang_combo.addItem(label, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData("en"))
        row=0
        cfg_layout.addWidget(QLabel(T(self.lang,"Sample folder")), row,0)
        folder_row = QHBoxLayout(); folder_row.addWidget(self.path_edit,1); folder_row.addWidget(self.browse_btn,0)
        cfg_layout.addLayout(folder_row, row,1); row += 1
        cfg_layout.addWidget(self.warn_label, row,0,1,2); row += 1
        cfg_layout.addWidget(QLabel(T(self.lang,"Starting note")), row,0); cfg_layout.addWidget(self.note_combo,row,1); row += 1
        cfg_layout.addWidget(QLabel(T(self.lang,"Starting octave")), row,0); cfg_layout.addWidget(self.octave_combo,row,1); row += 1
        cfg_layout.addWidget(QLabel(T(self.lang,"Semitone range")), row,0); cfg_layout.addWidget(self.range_spin,row,1); row += 1
        cfg_layout.addWidget(QLabel(T(self.lang,"Gap (seconds)")), row,0); cfg_layout.addWidget(self.gap_spin,row,1); row += 1
        cfg_layout.addWidget(self.opt_pitched, row,0,1,2); row += 1
        cfg_layout.addWidget(self.opt_dump, row,0,1,2); row += 1
        cfg_layout.addWidget(self.opt_random, row,0,1,2); row += 1
        cfg_layout.addWidget(self.opt_normalize, row,0,1,2); row += 1
        appearance_row = QHBoxLayout()
        appearance_row.addWidget(QLabel("Theme:")); appearance_row.addWidget(self.mode_combo)
        appearance_row.addSpacing(12)
        appearance_row.addWidget(QLabel("Accent:")); appearance_row.addWidget(self.accent_combo)
        appearance_row.addSpacing(12)
        appearance_row.addWidget(QLabel("Language:")); appearance_row.addWidget(self.lang_combo)
        appearance_row.addStretch(1)
        cfg_layout.addLayout(appearance_row, row,0,1,2); row += 1
        run_group = QGroupBox(T(self.lang,"Run")); run_layout = QVBoxLayout(run_group)
        btns_row = QHBoxLayout()
        self.generate_btn = QPushButton(T(self.lang,"Generate Chromatic")); self.generate_btn.setEnabled(False)
        self.cancel_btn = QPushButton(T(self.lang,"Cancel")); self.cancel_btn.setEnabled(False)
        self.open_out_btn = QPushButton(T(self.lang,"Open Output Folder")); self.open_out_btn.setEnabled(False)
        btns_row.addWidget(self.generate_btn); btns_row.addWidget(self.cancel_btn); btns_row.addWidget(self.open_out_btn)
        run_layout.addLayout(btns_row)
        self.progress = QProgressBar(); self.progress.setRange(0,100); self.progress.setValue(0)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setPlaceholderText(T(self.lang,"Logs will appear here…"))
        run_layout.addWidget(self.progress); run_layout.addWidget(self.log,1)
        footer_row = QHBoxLayout()
        self.footer = QLabel(T(self.lang,"Footer")); self.footer.setObjectName("Footer")
        self.credits_btn = QPushButton(T(self.lang,"Credits")); self.credits_btn.setObjectName("LinkButton")
        footer_row.addWidget(self.footer,1); footer_row.addStretch(1); footer_row.addWidget(self.credits_btn,0)
        outer = QVBoxLayout(central); inner = QHBoxLayout()
        inner.addWidget(cfg_group,1); inner.addWidget(run_group,1)
        outer.addLayout(inner,1); outer.addLayout(footer_row)
        help_menu = self.menuBar().addMenu(T(self.lang,"&Help"))
        act_credits = QAction(T(self.lang,"Credits"), self); act_credits.triggered.connect(self.show_credits)
        help_menu.addAction(act_credits)
        self.setStatusBar(QStatusBar()); self.apply_theme()
        self.path_edit.textChanged.connect(self.refresh_validation)
        self.mode_combo.currentTextChanged.connect(self.on_theme_changed)
        self.accent_combo.currentTextChanged.connect(self.on_theme_changed)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        self.generate_btn.clicked.connect(self.start_generation)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.open_out_btn.clicked.connect(self.open_output_folder_clicked)
        self.credits_btn.clicked.connect(self.show_credits)
        self.worker: GenerateWorker | None = None
        self.last_output_path: Path | None = None
        self.setAcceptDrops(True); self.refresh_validation(); self.refresh_button_state()

    def apply_theme(self): self.setStyleSheet(build_stylesheet(self.mode,self.accent))
    def on_theme_changed(self):
        self.mode = self.mode_combo.currentText(); self.accent = self.accent_combo.currentText(); self.apply_theme()

    def on_language_changed(self):
        code = self.lang_combo.currentData()
        if code and code != self.lang:
            self.lang = code; self.retranslate_all()

    def retranslate_all(self):
        self.setWindowTitle(APP_TITLE)
        self.findChild(QGroupBox).setTitle(T(self.lang,"Configuration"))
        self.browse_btn.setText(T(self.lang,"Browse…"))
        self.path_edit.setPlaceholderText(T(self.lang,"Select a folder containing 1.wav, 2.wav, ..."))
        self.opt_pitched.setText(T(self.lang,"Apply pitch transformation"))
        self.opt_dump.setText(T(self.lang,"Dump individual pitched samples"))
        self.opt_random.setText(T(self.lang,"Randomize sample selection"))
        self.opt_normalize.setText(T(self.lang,"Peak normalize each sample (pre-pitch)"))
        self.generate_btn.setText(T(self.lang,"Generate Chromatic"))
        self.cancel_btn.setText(T(self.lang,"Cancel"))
        self.open_out_btn.setText(T(self.lang,"Open Output Folder"))
        self.credits_btn.setText(T(self.lang,"Credits"))
        self.footer.setText(T(self.lang,"Footer"))
        self.menuBar().clear()
        help_menu = self.menuBar().addMenu(T(self.lang,"&Help"))
        act_credits = QAction(T(self.lang,"Credits"), self); act_credits.triggered.connect(self.show_credits)
        help_menu.addAction(act_credits)
        self.refresh_validation()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dropEvent(self, event):
        urls = event.mimeData().urls(); 
        if not urls: return
        p = urls[0].toLocalFile()
        if os.path.isdir(p): self.path_edit.setText(p)

    def show_error(self, msg: str): QMessageBox.critical(self, APP_TITLE, msg)
    def show_info(self, msg: str): QMessageBox.information(self, APP_TITLE, msg)
    def ask_yes_no(self, title: str, question: str) -> bool:
        ret = QMessageBox.question(self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return ret == QMessageBox.Yes

    def folder_valid(self) -> bool:
        p = Path(self.path_edit.text().strip())
        return p.exists() and p.is_dir() and (p / "1.wav").exists()

    def refresh_validation(self):
        if not self.path_edit.text().strip():
            self.warn_label.setVisible(False)
        else:
            p = Path(self.path_edit.text().strip())
            if not p.exists() or not p.is_dir():
                self.warn_label.setText(T(self.lang,"Folder not found.")); self.warn_label.setVisible(True)
            elif not (p / "1.wav").exists():
                self.warn_label.setText(T(self.lang,"Need at least 1.wav in this folder.")); self.warn_label.setVisible(True)
            else:
                idx = 1
                while (p / f"{idx}.wav").exists(): idx += 1
                if idx == 1:
                    self.warn_label.setText(T(self.lang,"No sequential samples found (1.wav, 2.wav, ...).")); self.warn_label.setVisible(True)
                else:
                    self.warn_label.setVisible(False)
        self.refresh_button_state()

    def refresh_button_state(self):
        ok = self.folder_valid() and self.range_spin.value() > 0 and (0.0 <= self.gap_spin.value() <= MAX_GAP_SEC)
        self.generate_btn.setEnabled(ok and (self.worker is None))
        self.cancel_btn.setEnabled(self.worker is not None)
        self.open_out_btn.setEnabled(self.last_output_path is not None and os.path.exists(self.last_output_path))

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, T(self.lang,"Select Sample Folder"), os.path.expanduser("~"))
        if path:
            self.path_edit.setText(path)
            self.statusBar().showMessage(T(self.lang,"Selected folder: {p}", p=path), 5000)

    def open_output_folder_clicked(self):
        if not self.last_output_path or not os.path.exists(self.last_output_path):
            self.show_info(T(self.lang,"No output file yet.")); return
        self.open_output_folder(self.last_output_path)

    def open_output_folder(self, filepath: str | Path):
        fp = str(filepath)
        if os.path.exists(fp):
            try: subprocess.Popen(f'explorer /select,"{fp}"')
            except Exception: subprocess.Popen(["explorer", os.path.dirname(fp)])

    def show_credits(self):
        dlg = CreditsDialog(self.lang, self); dlg.exec()

    @Slot()
    def start_generation(self):
        if not self.folder_valid():
            self.show_error(T(self.lang,"Invalid folder. Place '1.wav', '2.wav', ... in it.")); return
        sample_path = Path(self.path_edit.text().strip())
        out_path = sample_path / "chromatic.wav"
        if out_path.exists():
            if not self.ask_yes_no(APP_TITLE, T(self.lang,"'{name}' already exists. Overwrite?", name=out_path.name)):
                self.statusBar().showMessage(T(self.lang,"Cancelled by user."), 5000); return
        semitones = int(self.range_spin.value()); gap_seconds = float(self.gap_spin.value())
        pitched = self.opt_pitched.isChecked(); dump_samples = self.opt_dump.isChecked()
        randomize = self.opt_random.isChecked(); normalize = self.opt_normalize.isChecked()
        start_note_index = self.note_combo.currentIndex(); start_octave = int(self.octave_combo.currentText())
        self.log.clear(); self.progress.setValue(0)
        self.worker = GenerateWorker(sample_path, semitones, gap_seconds, pitched, dump_samples, randomize,
                                     start_note_index, start_octave, normalize, self.lang)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.append_log)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.finished.connect(self.on_worker_finished)
        self.generate_btn.setEnabled(False); self.cancel_btn.setEnabled(True); self.open_out_btn.setEnabled(False)
        self.statusBar().showMessage(T(self.lang,"Generating…")); self.worker.start()

    @Slot()
    def cancel_generation(self):
        if self.worker: self.worker.request_cancel(); self.statusBar().showMessage(T(self.lang,"Cancelling…"))

    @Slot(str)
    def append_log(self, text: str):
        self.log.append(text); self.log.moveCursor(self.log.textCursor().End)

    @Slot()
    def on_worker_finished(self):
        self.worker = None; self.refresh_button_state()

    @Slot(str)
    def on_done(self, out_path: str):
        self.statusBar().showMessage(T(self.lang,"Done! Saved to {p}", p=out_path), 8000)
        self.append_log(T(self.lang,"✅ Completed! Output: {p}", p=out_path))
        self.progress.setValue(100); self.last_output_path = Path(out_path); self.open_out_btn.setEnabled(True)

    @Slot(str)
    def on_error(self, msg: str):
        self.statusBar().showMessage(T(self.lang,"An error occurred."), 8000)
        self.append_log(T(self.lang,"❌ Error: {m}", m=msg))
        self.show_error(msg)

    @Slot(str)
    def on_cancelled(self, msg: str):
        self.statusBar().showMessage(msg, 8000)
        self.append_log(T(self.lang,"⚠️ Generation was cancelled."))
        self.progress.setValue(0)

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
