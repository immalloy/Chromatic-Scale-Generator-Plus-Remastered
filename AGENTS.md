# Agent Guidelines for Chromatic Scale Generator PLUS! (Remastered)

## Scope
These instructions apply to the entire repository unless a nested `AGENTS.md` overrides them.

## Project Overview
This project is a PySide6 desktop application for generating chromatic scales for Friday Night Funkin'.
* Entry point: `CSGPR.py` which imports `csgpr.app:main`.
* Core UI logic lives in `csgpr/main_window.py`.
* Internationalisation utilities live in `i18n_pkg/`.

## Coding Standards
* Target **Python 3.10+**. Prefer modern syntax (type hints, dataclasses, `pathlib` where reasonable).
* Follow PEP 8 spacing (4-space indentation, max ~100 characters per line to keep UI strings readable).
* Keep imports ordered: standard library, third-party, then local modules. Avoid unused imports.
* Do not wrap imports in `try/except`; guard optional features inside functions instead.
* When adding Qt widgets, connect signals in the constructor and prefer descriptive attribute names.

## UI & Internationalisation
* Any new user-facing string must be wrapped with `i18n_pkg.T(lang, ...)` and added to each language file in `i18n_pkg/`. Use the English file as the source of truth.
* When changing layouts, ensure widgets are added to the correct layout and that tab order remains intuitive.
* Keep stylesheet logic in `csgpr/styles.py` where possible instead of inline styles.
* For dialogs or message boxes, centralise logic in `csgpr/dialogs.py` unless a new dialog type is clearly isolated.

## Audio Generation Logic
* Long-running tasks should stay in worker threads (see `csgpr/generation.py`). If adding new work, ensure signals are emitted safely to the main thread.
* Validate file system paths with `pathlib.Path` and show user-friendly errors via the dialog helpers.

## Testing & Verification
* Manual run command: `python CSGPR.py`.
* When touching build scripts, confirm `build_CSGPR.bat` and `run_with_logs.bat` usage instructions remain valid.
* Prefer unit-testable helper functions; guard GUI-dependent code with `if __name__ == "__main__":` in scripts.

## Documentation & Metadata
* Update `README.md` if you introduce notable features or new requirements.
* Keep version badges in sync with actual release metadata when bumping versions.

