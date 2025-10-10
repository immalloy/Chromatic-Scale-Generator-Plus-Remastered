from __future__ import annotations

"""Background worker that generates chromatic scales."""

import math
import random
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import numpy as np
import parselmouth
from PySide6.QtCore import QThread, Signal

from i18n_pkg import T

from .constants import DEFAULT_SR, NOTE_NAMES


@dataclass(frozen=True)
class SliceMarker:
    """Slice marker information for exported WAV files."""

    offset: int
    label: str


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
        slicex_markers: bool,
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
        self.slicex_markers = slicex_markers
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
            markers: List[SliceMarker] = []
            starting_key = self.start_note_index + 12 * (self.start_octave - 2)
            gap_samples = int(gap.get_number_of_samples())
            current_offset = 0

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
                target_frequency = self._note_frequency(i)

                if self.normalize:
                    arr = snd.values.copy()
                    peak = float(np.max(np.abs(arr)))
                    if peak > 0:
                        arr = arr / peak
                        snd.values[:] = arr
                    self._emit("  • " + T(self.lang, "normalized"))

                if self.pitched:
                    manipulation = parselmouth.praat.call(
                        snd,
                        "To Manipulation",
                        0.05,
                        20.0 if target_frequency < 60.0 else 60.0,
                        600,
                    )
                    pitch_tier = parselmouth.praat.call(
                        manipulation, "Extract pitch tier"
                    )
                    start_time = float(snd.xmin)
                    end_time = float(snd.xmax)
                    if end_time <= start_time:
                        end_time = start_time + (1.0 / DEFAULT_SR)

                    num_points = int(
                        parselmouth.praat.call(pitch_tier, "Get number of points")
                    )

                    if num_points == 0:
                        pitch_tier = parselmouth.praat.call(
                            "Create PitchTier",
                            "TargetPitchTier",
                            start_time,
                            end_time,
                        )
                        parselmouth.praat.call(
                            pitch_tier, "Add point...", start_time, target_frequency
                        )
                        parselmouth.praat.call(
                            pitch_tier, "Add point...", end_time, target_frequency
                        )
                    else:
                        def ensure_point(point_time: float) -> None:
                            index = parselmouth.praat.call(
                                pitch_tier, "Get low index from time", point_time
                            )
                            if index != 0:
                                existing_time = float(
                                    parselmouth.praat.call(
                                        pitch_tier, "Get time of point", index
                                    )
                                )
                                if math.isclose(existing_time, point_time, abs_tol=1e-6):
                                    return
                            parselmouth.praat.call(
                                pitch_tier, "Add point...", point_time, target_frequency
                            )

                        ensure_point(start_time)
                        ensure_point(end_time)

                        parselmouth.praat.call(
                            pitch_tier,
                            "Formula",
                            f"{target_frequency}",
                        )
                    parselmouth.praat.call(
                        [pitch_tier, manipulation], "Replace pitch tier"
                    )
                    resynth = parselmouth.praat.call(
                        manipulation, "Get resynthesis (overlap-add)"
                    )
                    current_sound = resynth
                else:
                    current_sound = snd

                pitched_sounds.append(current_sound)
                spaced_sounds.append(current_sound)

                if self.slicex_markers:
                    label = self._note_label(i)
                    markers.append(SliceMarker(offset=current_offset, label=label))

                current_offset += int(current_sound.get_number_of_samples())

                spaced_sounds.append(gap)
                current_offset += gap_samples
                pct = int(((i + 1) / self.semitones) * 90)
                self.progress.emit(min(99, max(1, pct)))

            if self._cancel:
                self.cancelled.emit(T(self.lang, "Cancelled by user."))
                return

            self._emit(T(self.lang, "Concatenating chromatic scale..."))
            chromatic = parselmouth.Sound.concatenate(spaced_sounds)
            out_path = self.sample_path / "chromatic.wav"
            if self.slicex_markers:
                self._emit(
                    T(self.lang, "Embedding FL Studio Slicex slice markers...")
                )
                save_sound_with_markers(chromatic, out_path, markers)
            else:
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

    def _note_label(self, index: int) -> str:
        total = self.start_note_index + index
        name = NOTE_NAMES[total % len(NOTE_NAMES)]
        octave = self.start_octave + (total // len(NOTE_NAMES))
        return f"{name}{octave}"

    def _note_frequency(self, index: int) -> float:
        """Return the equal temperament frequency for the note at ``index``.

        Notes are calculated relative to ``A4`` (MIDI note 69) at 440 Hz. The
        ``start_note_index`` and ``start_octave`` determine the MIDI note number
        for the first generated note, and ``index`` acts as the semitone offset
        from that starting point.
        """

        base_midi = (self.start_octave + 1) * 12 + self.start_note_index
        midi_note = base_midi + index
        return 440.0 * math.pow(2.0, (midi_note - 69) / 12.0)


__all__ = ["GenerateWorker"]


def _pack_chunk(chunk_id: bytes, body: bytes) -> bytes:
    chunk = chunk_id + struct.pack("<I", len(body)) + body
    if len(body) % 2 == 1:
        chunk += b"\x00"
    return chunk


def save_sound_with_markers(
    sound: parselmouth.Sound, out_path: Path, markers: Sequence[SliceMarker]
) -> None:
    if not markers:
        sound.save(str(out_path), "WAV")
        return

    sr = int(sound.sampling_frequency)
    channels = int(sound.get_number_of_channels())

    values = np.asarray(sound.values)
    clipped = np.clip(values, -1.0, 1.0)
    pcm = np.rint(clipped * 32767.0).astype("<i2")
    interleaved = np.ascontiguousarray(np.transpose(pcm))
    data_bytes = interleaved.tobytes()

    byte_rate = sr * channels * 2
    block_align = channels * 2
    fmt_body = struct.pack("<HHIIHH", 1, channels, sr, byte_rate, block_align, 16)
    fmt_chunk = _pack_chunk(b"fmt ", fmt_body)
    data_chunk = _pack_chunk(b"data", data_bytes)

    cue_body = struct.pack("<I", len(markers))
    list_body = b"adtl"

    for cue_id, marker in enumerate(markers, start=1):
        sample_offset = max(0, int(marker.offset))
        cue_body += struct.pack(
            "<II4sIII", cue_id, sample_offset, b"data", 0, 0, sample_offset
        )

        label_text = marker.label.encode("utf-8") + b"\x00"
        label_body = struct.pack("<I", cue_id) + label_text
        list_body += _pack_chunk(b"labl", label_body)

    cue_chunk = _pack_chunk(b"cue ", cue_body)
    list_chunk = _pack_chunk(b"LIST", list_body)

    riff_body = b"WAVE" + fmt_chunk + data_chunk + cue_chunk + list_chunk
    riff_chunk = b"RIFF" + struct.pack("<I", len(riff_body)) + riff_body

    with open(out_path, "wb") as handle:
        handle.write(riff_chunk)
