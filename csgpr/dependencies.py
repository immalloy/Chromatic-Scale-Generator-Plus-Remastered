from __future__ import annotations

"""Helpers for validating runtime dependencies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    module: str
    pip_name: str | None = None


_REQUIRED: tuple[Requirement, ...] = (
    Requirement("numpy"),
    Requirement("PySide6"),
    Requirement("parselmouth", "praat-parselmouth"),
)


def _require(req: Requirement) -> None:
    try:
        __import__(req.module)
    except ImportError as exc:  # pragma: no cover - runtime guard
        pkg = req.pip_name or req.module
        raise SystemExit(
            f"Missing dependency: {req.module}\n"
            f"Fix with:  pip install {pkg}\n"
        ) from exc


def ensure_dependencies() -> None:
    """Ensure that all runtime dependencies are importable."""
    for requirement in _REQUIRED:
        _require(requirement)
