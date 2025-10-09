from __future__ import annotations

"""Background worker that generates chromatic scales."""

import random
from pathlib import Path
from typing import List

import numpy as np
import parselmouth
from PySide6.QtCore import QThread, Signal

from i18n_pkg import T

from .constants import DEFAULT_SR


class GenerateWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    done = Signal(str)
    error = Signal(str)
    cancelled = Signal(str)

    def __init__(
        self,
        sample_path: Path,
        semitones: int,
        gap_seconds: float,
        pitched: bool,
        dump_samples: bool,
        randomize: bool,
        start_note_index: int,
        start_octave: int,
        normalize: bool,
        lang: str,
        parent=None,
    ) -> None:
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

    def request_cancel(self) -> None:
        self._cancel = True

    def _emit(self, text: str) -> None:
        self.log.emit(text)

    def run(self) -> None:  # pragma: no cover - GUI thread
        try:
            if not self.sample_path.exists():
                raise FileNotFoundError(T(self.lang, "Folder not found."))

            file_count = 0
            while (self.sample_path / f"{file_count + 1}.wav").exists():
                file_count += 1

            if file_count == 0:
                raise FileNotFoundError(
                    T(self.lang, "No sequential samples found (1.wav, 2.wav, ...).")
                )

            self._emit(
                T(
                    self.lang,
                    "Found {n} sample(s) (1.wav..{m}.wav).",
                    n=file_count,
                    m=file_count,
                )
            )
            self._emit(
                T(
                    self.lang,
                    "Semitones: {s} | Gap: {g:.3f}s | Pitched: {p}",
                    s=self.semitones,
                    g=self.gap_seconds,
                    p=self.pitched,
                )
            )
            if self.normalize:
                self._emit(T(self.lang, "Peak normalization: ON"))

            gap = parselmouth.praat.call(
                "Create Sound from formula",
                "Gap",
                1,
                0,
                float(self.gap_seconds),
                DEFAULT_SR,
                "0",
            )
            pitched_sounds: List[parselmouth.Sound] = []
            spaced_sounds: List[parselmouth.Sound] = []
            starting_key = self.start_note_index + 12 * (self.start_octave - 2)

            for i in range(self.semitones):
                if self._cancel:
                    self.cancelled.emit(T(self.lang, "Cancelled by user."))
                    return

                idx = (
                    random.randint(1, file_count)
                    if self.randomize
                    else (i % file_count) + 1
                )
                file_path = self.sample_path / f"{idx}.wav"
                self._emit(
                    T(
                        self.lang,
                        "[{a}/{b}] Loading {name}",
                        a=i + 1,
                        b=self.semitones,
                        name=file_path.name,
                    )
                )
                snd = parselmouth.Sound(str(file_path))
                snd = parselmouth.praat.call(snd, "Resample", DEFAULT_SR, 1)
                snd = parselmouth.praat.call(snd, "Convert to mono")

                if self.normalize:
                    arr = snd.values.copy()
                    peak = float(np.max(np.abs(arr)))
                    if peak > 0:
                        arr = arr / peak
                        snd.values[:] = arr
                    self._emit("  • " + T(self.lang, "normalized"))

                if self.pitched:
                    manipulation = parselmouth.praat.call(
                        snd, "To Manipulation", 0.05, 60, 600
                    )
                    pitch_tier = parselmouth.praat.call(
                        manipulation, "Extract pitch tier"
                    )
                    parselmouth.praat.call(
                        pitch_tier,
                        "Formula",
                        f"32.703 * (2 ^ ({i + starting_key + 12}/12))",
                    )
                    parselmouth.praat.call(
                        [pitch_tier, manipulation], "Replace pitch tier"
                    )
                    resynth = parselmouth.praat.call(
                        manipulation, "Get resynthesis (overlap-add)"
                    )
                    pitched_sounds.append(resynth)
                    spaced_sounds.append(resynth)
                else:
                    pitched_sounds.append(snd)
                    spaced_sounds.append(snd)

                spaced_sounds.append(gap)
                pct = int(((i + 1) / self.semitones) * 90)
                self.progress.emit(min(99, max(1, pct)))

            if self._cancel:
                self.cancelled.emit(T(self.lang, "Cancelled by user."))
                return

            self._emit(T(self.lang, "Concatenating chromatic scale..."))
            chromatic = parselmouth.Sound.concatenate(spaced_sounds)
            out_path = self.sample_path / "chromatic.wav"
            chromatic.save(str(out_path), "WAV")
            self._emit(T(self.lang, "Saved: {path}", path=out_path))

            if self.dump_samples and self.pitched:
                dump_dir = self.sample_path / "pitched_samples"
                dump_dir.mkdir(exist_ok=True)
                for idx, sound in enumerate(pitched_sounds, start=1):
                    file_path = dump_dir / f"pitched_{idx}.wav"
                    sound.save(str(file_path), "WAV")
                self._emit(
                    T(
                        self.lang,
                        "Dumped {n} pitched sample(s) to: {dir}",
                        n=len(pitched_sounds),
                        dir=dump_dir,
                    )
                )

            self.progress.emit(100)
            self.done.emit(str(out_path))
        except Exception as exc:  # pragma: no cover - GUI thread
            self.error.emit(str(exc))
