from __future__ import annotations

"""Qt stylesheet helpers."""

from typing import Dict, Tuple

PaletteKey = Tuple[str, str]
Palette = Dict[str, str]


PALETTES: dict[PaletteKey, Palette] = {
    ("dark", "blue"): dict(
        bg="#121212",
        panel="#1A1A1A",
        text="#EDEDED",
        sub="#C9C9C9",
        field="#222222",
        border="#2F2F2F",
        accent="#2D7CF3",
        accent2="#5AA1FF",
        warn="#FFB3B3",
        muted="#9A9A9A",
    ),
    ("dark", "pink"): dict(
        bg="#121212",
        panel="#1A1A1A",
        text="#F4F1F6",
        sub="#D6B2C8",
        field="#222222",
        border="#2F2F2F",
        accent="#FF5AA1",
        accent2="#FF9AC0",
        warn="#FFC2D6",
        muted="#9A9A9A",
    ),
    ("light", "blue"): dict(
        bg="#F7F7FA",
        panel="#FFFFFF",
        text="#1B1B1B",
        sub="#5A5A5A",
        field="#FFFFFF",
        border="#D7D7DD",
        accent="#2D7CF3",
        accent2="#5AA1FF",
        warn="#B00020",
        muted="#6F6F77",
    ),
    ("light", "pink"): dict(
        bg="#FDF7FA",
        panel="#FFFFFF",
        text="#1B1B1B",
        sub="#7B5163",
        field="#FFFFFF",
        border="#E6D6DE",
        accent="#FF5AA1",
        accent2="#FF7EB9",
        warn="#B00020",
        muted="#6F6F77",
    ),
}


def build_stylesheet(mode: str, accent: str) -> str:
    palette = PALETTES[(mode, accent)]
    return f"""
        QMainWindow {{ background: {palette['bg']}; }}
        QGroupBox {{
            color: {palette['text']};
            border: 1px solid {palette['border']};
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            background: {palette['panel']};
        }}
        QLabel, QCheckBox, QStatusBar, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
            color: {palette['text']};
            font-size: 14px;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {{
            background: {palette['field']};
            border: 1px solid {palette['border']};
            border-radius: 8px;
            padding: 6px;
            color: {palette['text']};
        }}
        QPushButton {{
            background: {palette['accent']};
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            color: white;
            font-weight: 600;
        }}
        QPushButton:disabled {{ background: {palette['border']}; color: {palette['muted']}; }}
        QProgressBar {{
            background: {palette['field']};
            border: 1px solid {palette['border']};
            border-radius: 8px;
            text-align: center;
            color: {palette['text']};
            height: 18px;
        }}
        QProgressBar::chunk {{ border-radius: 8px; margin: 1px; background: {palette['accent2']}; }}
        #Footer {{ color: {palette['sub']}; font-size: 12px; padding: 8px 0; }}
        #WarnLabel {{ color: {palette['warn']}; font-size: 12px; }}
        #LinkButton {{ background: transparent; color: {palette['accent']}; border: none; text-decoration: underline; padding: 0px; font-weight: 600; }}
    """
