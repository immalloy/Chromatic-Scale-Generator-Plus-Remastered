from __future__ import annotations

"""Application entry point."""

import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .constants import APP_ICON_PATH
from .main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    try:
        if os.path.exists(APP_ICON_PATH):
            app.setWindowIcon(QIcon(APP_ICON_PATH))
    except Exception:  # pragma: no cover - environment specific
        pass

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


__all__ = ["main"]
