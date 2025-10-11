from __future__ import annotations

"""Custom order presets, templates, and resolver utilities.

This module implements the filename tag detection, preset serialization and
resolver logic required for the "Custom / Presets" mode. The code is designed
to be completely independent from Qt so it can be unit tested easily.
"""

from dataclasses import dataclass, field
import json
import random
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, MutableMapping, Optional, Sequence


SYMBOL_TAG_PATTERN = re.compile(r"__(?P<sym>[A-Za-z]+)(?=\.wav$)", re.IGNORECASE)
DEFAULT_SYMBOLS = ("A", "E", "I", "O", "U", "AY")


class PresetError(Exception):
    """Raised when a preset or template payload is invalid."""


class ResolutionError(Exception):
    """Raised when a preset cannot be resolved into a usable sequence."""

    def __init__(self, message: str, *, symbol: str | None = None) -> None:
        super().__init__(message)
        self.symbol = symbol


@dataclass(slots=True)
class SelectionPolicy:
    mode: str = "first"
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, object]:
        return {"mode": self.mode, "seed": self.seed}

    @classmethod
    def from_dict(cls, data: MutableMapping[str, object]) -> "SelectionPolicy":
        mode = str(data.get("mode", "first")).lower()
        seed_raw = data.get("seed")
        seed = int(seed_raw) if seed_raw is not None else None
        if mode not in {"first", "cycle", "random"}:
            raise PresetError(f"Unsupported selection policy: {mode}")
        return cls(mode=mode, seed=seed)


@dataclass(slots=True)
class CustomOrderPreset:
    name: str
    symbols: List[str]
    order: List[str]
    policy: SelectionPolicy = field(default_factory=SelectionPolicy)
    length_policy: str = "pad"
    on_missing_symbol: str = "skip"

    def validate(self) -> None:
        allowed = {symbol.upper() for symbol in self.symbols}
        if not allowed:
            raise PresetError("Preset must declare at least one allowed symbol")
        if not self.order:
            raise PresetError("Preset order cannot be empty")
        for token in self.order:
            if token.upper() not in allowed:
                raise PresetError(f"Unknown token in order: {token}")
        if self.length_policy not in {"pad", "truncate", "error"}:
            raise PresetError(f"Unsupported length policy: {self.length_policy}")
        if self.on_missing_symbol not in {"skip", "ask", "error"}:
            raise PresetError(
                f"Unsupported missing-symbol policy: {self.on_missing_symbol}"
            )

    def normalized(self) -> "CustomOrderPreset":
        return CustomOrderPreset(
            name=self.name,
            symbols=[s.upper() for s in self.symbols],
            order=[s.upper() for s in self.order],
            policy=self.policy,
            length_policy=self.length_policy.lower(),
            on_missing_symbol=self.on_missing_symbol.lower(),
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "symbols": [s.upper() for s in self.symbols],
            "order": [s.upper() for s in self.order],
            "policy": self.policy.to_dict(),
            "length_policy": self.length_policy,
            "on_missing_symbol": self.on_missing_symbol,
            "version": 1,
        }

    @classmethod
    def from_dict(cls, data: MutableMapping[str, object]) -> "CustomOrderPreset":
        try:
            name = str(data["name"])
            symbols = [str(s).upper() for s in data["symbols"]]  # type: ignore[index]
            order = [str(s).upper() for s in data["order"]]  # type: ignore[index]
        except KeyError as exc:  # pragma: no cover - defensive
            raise PresetError(f"Missing preset key: {exc.args[0]}") from exc

        policy = SelectionPolicy.from_dict(
            data.get("policy", {"mode": "first"})  # type: ignore[arg-type]
        )
        length_policy = str(data.get("length_policy", "pad")).lower()
        missing = str(data.get("on_missing_symbol", "skip")).lower()
        preset = cls(
            name=name,
            symbols=symbols,
            order=order,
            policy=policy,
            length_policy=length_policy,
            on_missing_symbol=missing,
        )
        preset.validate()
        return preset


@dataclass(slots=True)
class CustomTemplate:
    name: str
    preset: CustomOrderPreset
    settings: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "preset": self.preset.to_dict(),
            "settings": self.settings,
            "version": 1,
        }

    @classmethod
    def from_dict(cls, data: MutableMapping[str, object]) -> "CustomTemplate":
        try:
            name = str(data["name"])
            preset_dict = data["preset"]  # type: ignore[index]
            settings = dict(data.get("settings", {}))  # type: ignore[arg-type]
        except KeyError as exc:  # pragma: no cover - defensive
            raise PresetError(f"Missing template key: {exc.args[0]}") from exc
        preset = CustomOrderPreset.from_dict(preset_dict)  # type: ignore[arg-type]
        return cls(name=name, preset=preset, settings=settings)


@dataclass(slots=True)
class SymbolDetection:
    symbol: Optional[str]
    source: Optional[str]
    warning: Optional[str] = None


@dataclass(slots=True)
class BucketScanResult:
    buckets: Dict[str, List[Path]]
    unlabeled: List[Path]
    unknown_symbols: Dict[str, List[Path]]
    warnings: List[str]


@dataclass(slots=True)
class PreviewItem:
    token: str
    path: Optional[Path]
    note: Optional[str] = None


@dataclass(slots=True)
class ResolutionResult:
    sequence: List[Path]
    preview: List[PreviewItem]
    warnings: List[str]


_SCAN_CACHE: Dict[tuple[str, tuple], BucketScanResult] = {}


def detect_symbol(path: Path, allowed_symbols: Iterable[str]) -> SymbolDetection:
    allowed = {s.upper() for s in allowed_symbols}
    match = SYMBOL_TAG_PATTERN.search(path.name)
    tag_symbol = match.group("sym").upper() if match else None
    folder_symbol = path.parent.name.upper() if path.parent != path else None
    folder_symbol = folder_symbol if folder_symbol in allowed else None

    if tag_symbol and tag_symbol not in allowed:
        tag_symbol = None

    warning = None
    if tag_symbol:
        if folder_symbol and folder_symbol != tag_symbol:
            warning = (
                f"Filename tag overrides folder symbol for {path.name}: "
                f"{tag_symbol} (folder {folder_symbol})"
            )
        return SymbolDetection(symbol=tag_symbol, source="tag", warning=warning)

    if folder_symbol:
        return SymbolDetection(symbol=folder_symbol, source="folder", warning=None)

    return SymbolDetection(symbol=None, source=None, warning=None)


def _fingerprint(files: Sequence[Path], root: Path) -> tuple:
    entries: List[tuple[str, int]] = []
    for file in files:
        rel = str(file.relative_to(root))
        try:
            stamp = int(file.stat().st_mtime_ns)
        except FileNotFoundError:  # pragma: no cover - file disappeared mid-scan
            stamp = 0
        entries.append((rel, stamp))
    return tuple(sorted(entries))


def scan_symbol_buckets(
    root: Path,
    *,
    allowed_symbols: Sequence[str] = DEFAULT_SYMBOLS,
    use_cache: bool = True,
) -> BucketScanResult:
    root = root.resolve()
    if not root.exists():
        return BucketScanResult(buckets={}, unlabeled=[], unknown_symbols={}, warnings=[])

    allowed_order = tuple(dict.fromkeys(symbol.upper() for symbol in allowed_symbols))
    allowed_key = tuple(sorted(allowed_order))

    files = sorted(root.rglob("*.wav"))
    files = [file for file in files if file.name.lower() != "chromatic.wav"]
    key = (str(root), allowed_key, _fingerprint(files, root))
    if use_cache and key in _SCAN_CACHE:
        return _SCAN_CACHE[key]

    buckets: Dict[str, List[Path]] = {symbol: [] for symbol in allowed_order}
    unlabeled: List[Path] = []
    unknown: Dict[str, List[Path]] = {}
    warnings: List[str] = []

    for file in files:
        if file.suffix.lower() != ".wav":
            continue
        detection = detect_symbol(file, allowed_symbols)
        if detection.warning:
            warnings.append(detection.warning)
        symbol = detection.symbol
        if symbol:
            buckets.setdefault(symbol, []).append(file)
        else:
            match = SYMBOL_TAG_PATTERN.search(file.name)
            if match:
                sym = match.group("sym").upper()
                unknown.setdefault(sym, []).append(file)
            else:
                unlabeled.append(file)

    result = BucketScanResult(
        buckets=buckets,
        unlabeled=sorted(unlabeled),
        unknown_symbols={sym: sorted(paths) for sym, paths in unknown.items()},
        warnings=warnings,
    )
    if use_cache:
        _SCAN_CACHE[key] = result
    return result


def _cycle_iterator(items: Sequence[Path]) -> Iterator[Path]:
    if not items:
        return iter(())
    while True:
        for item in items:
            yield item


def resolve_sequence(
    preset: CustomOrderPreset,
    buckets: MutableMapping[str, Sequence[Path]],
    *,
    target_length: int,
) -> ResolutionResult:
    preset = preset.normalized()
    preset.validate()

    order = [token.upper() for token in preset.order]
    preview: List[PreviewItem] = []
    warnings: List[str] = []
    sequence: List[Path] = []

    rng = random.Random(preset.policy.seed) if preset.policy.mode == "random" else None
    cycle_state: Dict[str, Iterator[Path]] = {}

    def pick(symbol: str) -> Optional[Path]:
        pool = list(buckets.get(symbol, ()))
        if not pool:
            return None
        if preset.policy.mode == "first":
            return pool[0]
        if preset.policy.mode == "cycle":
            if symbol not in cycle_state:
                cycle_state[symbol] = _cycle_iterator(pool)
            return next(cycle_state[symbol])
        assert preset.policy.mode == "random"
        assert rng is not None
        return rng.choice(pool)

    tokens_processed = 0
    tokens_per_pass = len(order)
    if tokens_per_pass == 0:
        raise ResolutionError("Preset order cannot be empty")

    previous_length = -1

    def handle_missing(symbol: str) -> None:
        message = f"Missing symbol {symbol}"
        if preset.on_missing_symbol == "error":
            raise ResolutionError(message, symbol=symbol)
        if preset.on_missing_symbol == "ask":
            raise ResolutionError("User confirmation required", symbol=symbol)
        warnings.append(message)

    while True:
        if preset.length_policy == "truncate" and tokens_processed >= tokens_per_pass:
            break
        token = order[tokens_processed % tokens_per_pass]
        tokens_processed += 1
        result = pick(token)
        if result is None:
            handle_missing(token)
            preview.append(PreviewItem(token=token, path=None, note="skipped"))
        else:
            preview.append(PreviewItem(token=token, path=result, note=None))
            sequence.append(result)

        if preset.length_policy in {"pad", "error"}:
            if len(sequence) >= target_length:
                break
            if tokens_processed % tokens_per_pass == 0:
                if len(sequence) == previous_length:
                    raise ResolutionError(
                        "Unable to fill sequence with available symbols"
                    )
                previous_length = len(sequence)
        elif preset.length_policy == "truncate" and tokens_processed >= tokens_per_pass:
            break

        if preset.length_policy == "truncate" and len(sequence) >= target_length:
            break

        if tokens_processed > target_length * max(1, tokens_per_pass) * 2:
            raise ResolutionError("Resolution loop guard triggered")

    if preset.length_policy == "pad" and len(sequence) < target_length:
        raise ResolutionError("Unable to pad sequence to requested length")

    if preset.length_policy == "error" and len(sequence) != target_length:
        raise ResolutionError("Resolved length does not match target")

    if preset.length_policy == "pad":
        sequence = sequence[:target_length]
        preview = preview[: target_length]
    elif preset.length_policy == "truncate" and len(sequence) > target_length:
        sequence = sequence[:target_length]
        preview = preview[: target_length]

    return ResolutionResult(sequence=sequence, preview=preview, warnings=warnings)


def export_preset(preset: CustomOrderPreset, path: Path) -> None:
    preset.validate()
    path.write_text(json.dumps(preset.to_dict(), indent=2), encoding="utf-8")


def import_preset(path: Path) -> CustomOrderPreset:
    data = json.loads(path.read_text(encoding="utf-8"))
    return CustomOrderPreset.from_dict(data)


def export_template(template: CustomTemplate, path: Path) -> None:
    template.preset.validate()
    path.write_text(json.dumps(template.to_dict(), indent=2), encoding="utf-8")


def import_template(path: Path) -> CustomTemplate:
    data = json.loads(path.read_text(encoding="utf-8"))
    return CustomTemplate.from_dict(data)


def build_default_sequence(
    file_count: int,
    semitones: int,
    *,
    randomize: bool,
    seed: Optional[int] = None,
) -> List[int]:
    if file_count <= 0:
        return []
    if randomize:
        rng = random.Random(seed)
        return [rng.randint(1, file_count) for _ in range(semitones)]
    return [((i % file_count) + 1) for i in range(semitones)]


__all__ = [
    "BucketScanResult",
    "CustomOrderPreset",
    "CustomTemplate",
    "DEFAULT_SYMBOLS",
    "PresetError",
    "PreviewItem",
    "ResolutionError",
    "ResolutionResult",
    "SelectionPolicy",
    "build_default_sequence",
    "detect_symbol",
    "export_preset",
    "export_template",
    "import_preset",
    "import_template",
    "resolve_sequence",
    "scan_symbol_buckets",
]
