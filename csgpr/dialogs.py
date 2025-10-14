from __future__ import annotations

"""Standalone Qt dialogs used by the application."""

import json
import subprocess
from pathlib import Path
from typing import Iterable

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
        contributors, github_error = self._fetch_contributors_from_github()
        if contributors:
            return contributors, False

        git_contributors, git_error = self._fetch_contributors_from_git()
        if git_contributors:
            return git_contributors, False

        return [], github_error or git_error

    def _fetch_contributors_from_github(self) -> tuple[list[str], bool]:
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        url = (
            "https://api.github.com/repos/"
            "immalloy/Chromatic-Scale-Generator-Plus-Remastered/contributors"
            "?per_page=100&anon=1"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Chromatic-Scale-Generator-Plus-Remastered",
        }
        contributors: list[str] = []
        seen: set[str] = set()

        try:
            while url:
                request = Request(url, headers=headers)
                with urlopen(request, timeout=10) as response:
                    if response.status != 200:
                        return [], True

                    payload = json.loads(response.read().decode("utf-8"))
                    contributors.extend(
                        self._normalize_contributor_entries(payload, seen)
                    )

                    url = self._next_link_from_headers(response.headers.get("Link"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return [], True

        return contributors, False

    def _next_link_from_headers(self, link_header: str | None) -> str | None:
        if not link_header:
            return None
        for part in link_header.split(","):
            section = part.strip()
            if not section:
                continue
            if ";" not in section:
                continue
            url_part, rel_part = section.split(";", 1)
            if 'rel="next"' in rel_part:
                url_part = url_part.strip()
                if url_part.startswith("<") and url_part.endswith(">"):
                    return url_part[1:-1]
        return None

    def _normalize_contributor_entries(
        self, entries: Iterable[dict], seen: set[str]
    ) -> list[str]:
        normalized: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            login = entry.get("login")
            display = (
                login
                or entry.get("name")
                or entry.get("email")
                or entry.get("type")
            )
            if not display:
                continue
            if display in seen:
                continue
            seen.add(display)
            normalized.append(display)
        return normalized

    def _fetch_contributors_from_git(self) -> tuple[list[str], bool]:
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
