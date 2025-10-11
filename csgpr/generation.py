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
        *,
        mode: str = "normal",
        custom_sequence: Sequence[Path] | None = None,
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
        self.mode = mode
        self.custom_sequence = [Path(p) for p in custom_sequence or []]
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
            if self.mode == "custom":
                if not self.custom_sequence:
                    raise FileNotFoundError(T(self.lang, "Custom preset is empty."))
                missing = [p for p in self.custom_sequence if not Path(p).exists()]
                if missing:
                    raise FileNotFoundError(
                        T(
                            self.lang,
                            "Missing sample for custom preset: {p}",
                            p=missing[0],
                        )
                    )
                file_count = len({p.resolve() for p in self.custom_sequence})
                self._emit(
                    T(
                        self.lang,
                        "Custom order will use {n} file(s).",
                        n=len(self.custom_sequence),
                    )
                )
            else:
                while (self.sample_path / f"{file_count + 1}.wav").exists():
                    file_count += 1

                if file_count == 0:
                    raise FileNotFoundError(
                        T(
                            self.lang,
                            "No sequential samples found (1.wav, 2.wav, ...).",
                        )
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

            sequence = list(self.custom_sequence) if self.mode == "custom" else None

            for i in range(self.semitones):
                if self._cancel:
                    self.cancelled.emit(T(self.lang, "Cancelled by user."))
                    return

                if self.mode == "custom":
                    if sequence is None or i >= len(sequence):
                        raise RuntimeError("Custom sequence shorter than semitone count")
                    file_path = sequence[i]
                else:
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
                    current_sound = _retune_sound(snd, target_frequency)
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


def _retune_sound(sound: parselmouth.Sound, target_frequency: float) -> parselmouth.Sound:
    """Return ``sound`` retuned to ``target_frequency``.

    For frequencies below ~60 Hz the standard Praat manipulation approach tends
    to leave the waveform untouched, which is what caused the extremely low
    notes (``C1`` through ``G1``) to remain off pitch. To compensate we try a
    lightweight FFT-based retuning strategy for those frequencies before
    falling back to the traditional manipulation pipeline. If anything fails we
    simply return the original sound as a safe fallback.
    """

    if target_frequency < 60.0:
        retuned = _retune_with_fft(sound, target_frequency)
        if retuned is not None:
            return retuned

    return _retune_with_manipulation(sound, target_frequency)


def _retune_with_manipulation(
    sound: parselmouth.Sound, target_frequency: float
) -> parselmouth.Sound:
    duration = float(sound.get_total_duration())
    manipulation = parselmouth.praat.call(
        sound,
        "To Manipulation",
        0.05,
        20.0 if target_frequency < 60.0 else 60.0,
        600,
    )
    pitch_tier = parselmouth.praat.call(manipulation, "Extract pitch tier")
    parselmouth.praat.call(
        pitch_tier,
        "Remove points between",
        sound.xmin,
        sound.xmax,
    )
    start_time = float(sound.xmin)
    end_time = float(sound.xmax)
    parselmouth.praat.call(
        pitch_tier,
        "Add point",
        start_time,
        target_frequency,
    )
    if duration > 0.0 and end_time > start_time:
        parselmouth.praat.call(
            pitch_tier,
            "Add point",
            end_time,
            target_frequency,
        )
    else:
        parselmouth.praat.call(
            pitch_tier,
            "Add point",
            start_time + 1e-6,
            target_frequency,
        )
    parselmouth.praat.call([pitch_tier, manipulation], "Replace pitch tier")
    resynth = parselmouth.praat.call(
        manipulation, "Get resynthesis (overlap-add)"
    )
    return resynth


def _retune_with_fft(
    sound: parselmouth.Sound, target_frequency: float
) -> parselmouth.Sound | None:
    try:
        pitch = parselmouth.praat.call(sound, "To Pitch", 0.0, 5.0, 200.0)
        current = float(
            parselmouth.praat.call(pitch, "Get quantile", 0, 0, 0.5, "Hertz")
        )
    except Exception:
        return None

    if not current or math.isnan(current):
        return None

    ratio = float(target_frequency) / float(current)
    if not math.isfinite(ratio) or ratio <= 0:
        return None

    if abs(math.log2(ratio)) < 1e-4:
        return sound

    values = np.asarray(sound.values, dtype=np.float64)
    sr = int(sound.sampling_frequency)
    n_channels, frames = values.shape
    oversample = 8
    padded_length = frames * oversample
    freqs = np.fft.rfftfreq(padded_length, d=1.0 / sr)
    shifted_channels = []

    for channel in values:
        padded = np.pad(channel, (0, padded_length - frames))
        spectrum = np.fft.rfft(padded)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        scaled = freqs / ratio
        mag_shifted = np.interp(scaled, freqs, magnitude, left=0.0, right=0.0)
        phase_shifted = np.interp(scaled, freqs, phase, left=0.0, right=0.0)
        shifted_spec = mag_shifted * np.exp(1j * phase_shifted)
        shifted = np.fft.irfft(shifted_spec, padded_length)
        shifted_channels.append(shifted[:frames])

    shifted_array = np.vstack(shifted_channels)
    shifted_array = np.clip(shifted_array, -1.0, 1.0)
    return parselmouth.Sound(shifted_array, sampling_frequency=sr)


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
