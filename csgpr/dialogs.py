from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

import subprocess
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from i18n_pkg import T

from .constants import DISCORD_INVITE


class CreditsDialog(QDialog):
    def __init__(self, lang: str, parent=None) -> None:
        super().__init__(parent)
        self.lang = lang

        self.setWindowTitle(T(self.lang, "Credits"))
        self.setMinimumWidth(420)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)

        tabs = QTabWidget(self)
        tabs.addTab(
            self._build_developers_section(),
            T(self.lang, "CreditsTabAbout"),
        )
        tabs.addTab(
            self._build_contributors_section(),
            T(self.lang, "CreditsTabContributors"),
        )
        layout.addWidget(tabs)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _build_developers_section(self) -> QWidget:
        widget = QWidget(self)
        section_layout = QVBoxLayout(widget)

        text = QLabel(T(self.lang, "CreditsText"))
        text.setWordWrap(True)
        section_layout.addWidget(text)

        buttons_row = QHBoxLayout()
        self.discord_btn = QPushButton(T(self.lang, "Join Discord"))
        self.discord_btn.setObjectName("LinkButton")
        self.discord_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DISCORD_INVITE))
        )
        buttons_row.addWidget(self.discord_btn)
        buttons_row.addStretch(1)
        section_layout.addLayout(buttons_row)
        section_layout.addStretch(1)
        return widget

    def _build_contributors_section(self) -> QWidget:
        widget = QWidget(self)
        section_layout = QVBoxLayout(widget)

        self.contributors_status = QLabel(T(self.lang, "CreditsContributorsLoading"))
        self.contributors_status.setWordWrap(True)
        section_layout.addWidget(self.contributors_status)

        self.contributors_text = QTextEdit(self)
        self.contributors_text.setReadOnly(True)
        self.contributors_text.setLineWrapMode(QTextEdit.NoWrap)
        self.contributors_text.setVisible(False)
        section_layout.addWidget(self.contributors_text)

        section_layout.addStretch(1)

        self._populate_contributors()
        return widget

    def _populate_contributors(self) -> None:
        contributors, errored = self._fetch_contributors()
        if contributors:
            self.contributors_status.setVisible(False)
            self.contributors_text.setPlainText("\n".join(contributors))
            self.contributors_text.setVisible(True)
        elif errored:
            self.contributors_status.setText(
                T(self.lang, "CreditsContributorsError")
            )
        else:
            self.contributors_status.setText(
                T(self.lang, "CreditsContributorsNone")
            )

    def _fetch_contributors(self) -> tuple[list[str], bool]:
        repo_root = Path(__file__).resolve().parent.parent
        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "shortlog",
                    "-sne",
                    "HEAD",
                ],
                capture_output=True,
                check=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, OSError):
            return [], True

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        contributors: list[str] = []
        for line in lines:
            if "\t" in line:
                _, value = line.split("\t", 1)
                contributors.append(value)
            else:
                contributors.append(line)
        return contributors, False
