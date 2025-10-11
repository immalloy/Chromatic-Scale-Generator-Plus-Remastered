from __future__ import annotations

"""Qt stylesheet helpers for the Chromatic Scale Generator PLUS!"""

from dataclasses import dataclass
from typing import Dict

__all__ = ["DEFAULT_ACCENT", "VALID_ACCENTS", "build_stylesheet"]


@dataclass(frozen=True)
class AccentPalette:
    primary: str
    hover: str
    disabled: str
    outline: str
    subtle: str


BASE_COLORS: Dict[str, str] = {
    "window_bg": "#0E1018",
    "card_bg": "#171B26",
    "card_border": "#1F2433",
    "text_primary": "#F4F6FB",
    "text_secondary": "#A7ADC2",
    "field_bg": "#11141D",
    "field_border": "#262C3C",
    "divider": "#202638",
    "error": "#FF7A9E",
    "muted": "#8D94AA",
    "scroll_track": "#1B2130",
    "scroll_thumb": "#2C3244",
}

ACCENTS: Dict[str, AccentPalette] = {
    "pink": AccentPalette(
        primary="#FF4D8F",
        hover="#FF6AA7",
        disabled="#4B2E3D",
        outline="#FF9FC7",
        subtle="#E55D9C",
    ),
    "blue": AccentPalette(
        primary="#5B7CFF",
        hover="#7895FF",
        disabled="#2C3352",
        outline="#9DB2FF",
        subtle="#4D6AEB",
    ),
}

DEFAULT_ACCENT = "pink"
VALID_ACCENTS = tuple(ACCENTS.keys())


def build_stylesheet(accent: str = DEFAULT_ACCENT) -> str:
    palette = ACCENTS.get(accent, ACCENTS[DEFAULT_ACCENT])
    base = BASE_COLORS
    return f"""
        QMainWindow {{
            background-color: {base['window_bg']};
            color: {base['text_primary']};
            font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
        }}
        QWidget {{
            color: {base['text_primary']};
            font-size: 14px;
        }}
        #HeaderBar {{
            background: transparent;
        }}
        QLabel#HeaderTitle {{
            font-size: 24px;
            font-weight: 700;
            color: {base['text_primary']};
        }}
        QFrame#Divider {{
            border-top: 1px solid {base['divider']};
            margin-top: 12px;
        }}
        QFrame#CardFrame {{
            background-color: {base['card_bg']};
            border: 1px solid {base['card_border']};
            border-radius: 16px;
        }}
        QLabel#CardTitle {{
            font-size: 18px;
            font-weight: 600;
            color: {base['text_primary']};
        }}
        QLabel#CardSubtitle, QLabel#MutedLabel {{
            color: {base['text_secondary']};
            line-height: 1.4em;
        }}
        QLabel#SectionHeader {{
            color: {base['text_primary']};
            font-weight: 600;
            margin-top: 4px;
        }}
        QLabel#ValidationLabel {{
            color: {base['error']};
            font-size: 12px;
        }}
        QLabel#FooterLabel {{
            color: {base['muted']};
            font-size: 12px;
        }}
        QSplitter::handle {{
            background-color: {base['divider']};
            width: 2px;
        }}
        QSplitter::handle:hover {{
            background-color: {palette.subtle};
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
            background-color: {base['field_bg']};
            border: 1px solid {base['field_border']};
            border-radius: 10px;
            padding: 8px 12px;
            selection-background-color: {palette.hover};
            selection-color: {base['text_primary']};
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{
            border: 1px solid {palette.outline};
        }}
        QComboBox QAbstractItemView {{
            background: {base['card_bg']};
            border: 1px solid {base['card_border']};
            selection-background-color: {palette.hover};
            selection-color: {base['text_primary']};
        }}
        QPushButton {{
            font-weight: 600;
            border-radius: 24px;
            padding: 10px 18px;
        }}
        QPushButton#QuickActionAccent {{
            background-color: {palette.primary};
            color: #0E1018;
            border: none;
        }}
        QPushButton#QuickActionAccent:hover {{
            background-color: {palette.hover};
        }}
        QPushButton#QuickActionAccent:disabled {{
            background-color: {palette.disabled};
            color: {base['muted']};
        }}
        QPushButton#QuickActionLink,
        QPushButton#TertiaryAction {{
            background: transparent;
            color: {palette.primary};
            border: 1px solid transparent;
            padding: 8px 12px;
        }}
        QPushButton#QuickActionLink:hover,
        QPushButton#TertiaryAction:hover {{
            color: {palette.hover};
        }}
        QPushButton#SecondaryAction {{
            background: transparent;
            border: 1px solid {palette.primary};
            color: {palette.primary};
        }}
        QPushButton#SecondaryAction:hover {{
            border-color: {palette.hover};
            color: {palette.hover};
        }}
        QPushButton#PrimaryAction {{
            background-color: {palette.primary};
            color: #0E1018;
            border: none;
        }}
        QPushButton#PrimaryAction:hover {{
            background-color: {palette.hover};
        }}
        QPushButton:focus {{
            outline: none;
            border: 1px solid {palette.outline};
        }}
        QPushButton:disabled {{
            background-color: {palette.disabled};
            color: {base['muted']};
            border-color: {palette.disabled};
        }}
        QPushButton#TertiaryAction:disabled {{
            color: {base['muted']};
        }}
        QProgressBar {{
            background: {base['field_bg']};
            border: 1px solid {base['field_border']};
            border-radius: 10px;
            text-align: center;
            color: {base['text_primary']};
            height: 24px;
        }}
        QProgressBar::chunk {{
            border-radius: 10px;
            background: {palette.primary};
        }}
        QPlainTextEdit {{
            border-radius: 12px;
            padding: 12px;
        }}
        QScrollBar:vertical {{
            width: 12px;
            background: {base['scroll_track']};
            margin: 4px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background: {base['scroll_thumb']};
            border-radius: 6px;
        }}
        QScrollBar:horizontal {{
            height: 12px;
            background: {base['scroll_track']};
            margin: 4px;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background: {base['scroll_thumb']};
            border-radius: 6px;
        }}
        QCheckBox {{
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {base['field_border']};
            background: {base['field_bg']};
        }}
        QCheckBox::indicator:checked {{
            background: {palette.primary};
            border: 1px solid {palette.primary};
        }}
        QCheckBox::indicator:disabled {{
            background: {palette.disabled};
            border-color: {palette.disabled};
        }}
        QStatusBar {{
            background: {base['card_bg']};
            color: {base['text_secondary']};
            border-top: 1px solid {base['card_border']};
        }}
        QStatusBar::item {{ border: none; }}
        QToolTip {{
            background: {base['card_bg']};
            color: {base['text_primary']};
            border: 1px solid {base['card_border']};
            border-radius: 8px;
            padding: 6px 10px;
        }}
        QDialog {{
            background: {base['card_bg']};
            color: {base['text_primary']};
        }}
        QTabWidget::pane {{
            border: 1px solid {base['card_border']};
            border-radius: 12px;
            padding: 12px;
            background: {base['window_bg']};
        }}
        QTabBar::tab {{
            background: transparent;
            color: {base['text_secondary']};
            padding: 8px 16px;
            border: none;
        }}
        QTabBar::tab:selected {{
            color: {palette.primary};
        }}
    """
