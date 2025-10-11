from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from csgpr.custom_order import (
    DEFAULT_SYMBOLS,
    CustomOrderPreset,
    CustomTemplate,
    PresetError,
    ResolutionError,
    SelectionPolicy,
    build_default_sequence,
    export_preset,
    export_template,
    import_preset,
    import_template,
    resolve_sequence,
    scan_symbol_buckets,
)


def test_preset_round_trip(tmp_path: Path) -> None:
    preset = CustomOrderPreset(
        name="Verse 2",
        symbols=list(DEFAULT_SYMBOLS),
        order=["A", "E", "I", "O"],
        policy=SelectionPolicy(mode="cycle"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    export_path = tmp_path / "verse.csgorder.json"
    export_preset(preset, export_path)
    loaded = import_preset(export_path)
    assert loaded == preset


def test_template_round_trip(tmp_path: Path) -> None:
    preset = CustomOrderPreset(
        name="Memory",
        symbols=list(DEFAULT_SYMBOLS),
        order=["A", "E"],
        policy=SelectionPolicy(mode="first"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    template = CustomTemplate(
        name="MEM",
        preset=preset,
        settings={"semitones": 36, "mode": "custom", "preset": "Memory"},
    )
    export_path = tmp_path / "mem.csgtemplate.json"
    export_template(template, export_path)
    loaded = import_template(export_path)
    assert loaded == template


def test_resolve_policies(tmp_path: Path) -> None:
    files_a = [tmp_path / "A__take1.wav", tmp_path / "A__take2.wav"]
    files_b = [tmp_path / "B__take.wav"]
    buckets = {"A": files_a, "B": files_b}

    preset_first = CustomOrderPreset(
        name="First",
        symbols=["A", "B"],
        order=["A", "A", "B"],
        policy=SelectionPolicy(mode="first"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    result_first = resolve_sequence(preset_first, buckets, target_length=3)
    assert result_first.sequence == [files_a[0], files_a[0], files_b[0]]

    preset_cycle = CustomOrderPreset(
        name="Cycle",
        symbols=["A", "B"],
        order=["A", "A", "A", "A"],
        policy=SelectionPolicy(mode="cycle"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    result_cycle = resolve_sequence(preset_cycle, buckets, target_length=4)
    assert result_cycle.sequence == [files_a[0], files_a[1], files_a[0], files_a[1]]

    preset_random = CustomOrderPreset(
        name="Random",
        symbols=["A"],
        order=["A", "A", "A"],
        policy=SelectionPolicy(mode="random", seed=7),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    result_random = resolve_sequence(preset_random, {"A": files_a}, target_length=3)
    assert result_random.sequence == [files_a[1], files_a[0], files_a[1]]


def test_missing_symbol_skip(tmp_path: Path) -> None:
    files_a = [tmp_path / "voice__A.wav"]
    buckets = {"A": files_a}
    preset = CustomOrderPreset(
        name="Missing",
        symbols=["A", "Z"],
        order=["A", "Z", "A"],
        policy=SelectionPolicy(mode="first"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    result = resolve_sequence(preset, buckets, target_length=3)
    assert len(result.sequence) == 3
    assert all(path == files_a[0] for path in result.sequence if path)
    assert any(item.path is None and item.note == "skipped" for item in result.preview)


def test_conflict_resolution(tmp_path: Path) -> None:
    folder = tmp_path / "A"
    folder.mkdir()
    file_path = folder / "sample__E.wav"
    file_path.write_bytes(b"")
    scan = scan_symbol_buckets(tmp_path)
    assert scan.buckets.get("E")
    assert any("overrides" in warning for warning in scan.warnings)


def test_build_default_sequence_matches_legacy() -> None:
    assert build_default_sequence(3, 5, randomize=False) == [1, 2, 3, 1, 2]
    rng_sequence = build_default_sequence(3, 5, randomize=True, seed=42)
    # deterministic random selection with seed is stable
    assert rng_sequence == [3, 1, 1, 3, 2]


def test_scan_symbol_buckets_ignores_unknown(tmp_path: Path) -> None:
    (tmp_path / "voice__qq.wav").write_bytes(b"")
    result = scan_symbol_buckets(tmp_path)
    assert "QQ" in result.unknown_symbols
    assert result.buckets.get("A") == []


def test_import_fixture_files() -> None:
    base = Path("tests/fixtures")
    preset = import_preset(base / "verse2_cycle.csgorder.json")
    template = import_template(base / "mem_36semi_template.csgtemplate.json")
    assert preset.name == "Verse 2 Cycle"
    assert template.preset.order[0] == "A"


def test_example_assets_are_loadable() -> None:
    base = Path("assets/examples")
    preset = import_preset(base / "standard_cycle.csgorder.json")
    template = import_template(base / "cycle_36_template.csgtemplate.json")
    assert preset.order == ["A", "E", "I", "O", "U", "AY"]
    assert template.preset.policy.mode == "cycle"
    random_template = import_template(base / "random_bounce_template.csgtemplate.json")
    assert random_template.preset.policy.mode == "random"
    assert random_template.preset.policy.seed == 128


def test_resolve_error_on_missing_symbol_error(tmp_path: Path) -> None:
    preset = CustomOrderPreset(
        name="Strict",
        symbols=["A"],
        order=["A"],
        policy=SelectionPolicy(mode="first"),
        length_policy="error",
        on_missing_symbol="error",
    )
    with pytest.raises(ResolutionError):
        resolve_sequence(preset, {"A": []}, target_length=1)


def test_preset_validation_rejects_unknown_symbol() -> None:
    preset = CustomOrderPreset(
        name="Bad",
        symbols=["A"],
        order=["Q"],
        policy=SelectionPolicy(mode="first"),
        length_policy="pad",
        on_missing_symbol="skip",
    )
    with pytest.raises(PresetError):
        preset.validate()
