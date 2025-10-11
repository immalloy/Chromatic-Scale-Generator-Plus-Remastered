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
        bg="#FFFFFF",
        panel="#FFFFFF",
        text="#202124",
        sub="#3C404B",
        field="#FFFFFF",
        border="#CDD5E6",
        accent="#2D7CF3",
        accent2="#4D90FE",
        warn="#B3261E",
        muted="#5F6368",
    ),
    ("light", "pink"): dict(
        bg="#FFFFFF",
        panel="#FFFFFF",
        text="#2A1724",
        sub="#6B3B53",
        field="#FFFFFF",
        border="#E4CAD7",
        accent="#F44A91",
        accent2="#FF7FBF",
        warn="#B3261E",
        muted="#80616F",
    ),
}


def _encode_color(color: str) -> str:
    """Return a hex colour suitable for embedding in data URIs."""

    return color.replace("#", "%23")


def build_stylesheet(mode: str, accent: str) -> str:
    palette = PALETTES[(mode, accent)]
    highlight_text = "white" if mode == "dark" else palette["text"]
    arrow_color = _encode_color(palette["accent"])
    arrow_disabled = _encode_color(palette["border"])
    down_arrow = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'>"
        f"<path fill='{arrow_color}' d='M1 1.5L6 6.5L11 1.5Z'/></svg>"
    )
    down_arrow_disabled = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'>"
        f"<path fill='{arrow_disabled}' d='M1 1.5L6 6.5L11 1.5Z'/></svg>"
    )
    up_arrow = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'>"
        f"<path fill='{arrow_color}' d='M1 6.5L6 1.5L11 6.5Z'/></svg>"
    )
    up_arrow_disabled = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'>"
        f"<path fill='{arrow_disabled}' d='M1 6.5L6 1.5L11 6.5Z'/></svg>"
    )
    return f"""
        QMainWindow {{ background: {palette['bg']}; }}
        QWidget {{
            background: {palette['bg']};
            color: {palette['text']};
        }}
        QGroupBox {{
            color: {palette['text']};
            border: 1px solid {palette['border']};
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            background: {palette['panel']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            color: {palette['sub']};
            font-weight: 600;
        }}
        QLabel, QCheckBox, QStatusBar, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
            color: {palette['text']};
            font-size: 14px;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {{
            background: {palette['field']};
            border: 1px solid {palette['border']};
            border-radius: 8px;
            padding: 6px;
            color: {palette['text']};
            selection-background-color: {palette['accent2']};
            selection-color: {highlight_text};
        }}
        QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {{
            color: {palette['muted']};
        }}
        QComboBox {{
            padding-right: 40px;
        }}
        QSpinBox, QDoubleSpinBox {{
            padding-right: 36px;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {palette['accent']};
        }}
        QComboBox QAbstractItemView {{
            background: {palette['panel']};
            border: 1px solid {palette['border']};
            color: {palette['text']};
            selection-background-color: {palette['accent2']};
            selection-color: {highlight_text};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border: none;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            image: url({down_arrow});
            width: 12px;
            height: 8px;
            margin-right: 8px;
        }}
        QComboBox::down-arrow:disabled {{
            image: url({down_arrow_disabled});
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {palette['border']};
            background: transparent;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 28px;
            border-left: 1px solid {palette['border']};
            background: transparent;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: url({up_arrow});
            width: 12px;
            height: 8px;
        }}
        QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled {{
            image: url({up_arrow_disabled});
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: url({down_arrow});
            width: 12px;
            height: 8px;
        }}
        QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
            image: url({down_arrow_disabled});
        }}
        QPushButton {{
            background: {palette['accent']};
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            color: white;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {palette['accent2']}; }}
        QPushButton:pressed {{ background: {palette['accent']}; }}
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
        QStatusBar {{
            background: {palette['panel']};
            color: {palette['sub']};
            border-top: 1px solid {palette['border']};
        }}
        QStatusBar::item {{ border: none; }}
        QMenuBar {{
            background: {palette['panel']};
            color: {palette['text']};
            border-bottom: 1px solid {palette['border']};
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 4px 12px;
            margin: 0 4px;
            border-radius: 6px;
        }}
        QMenuBar::item:selected {{ background: {palette['accent2']}; color: {highlight_text}; }}
        QMenu {{
            background: {palette['panel']};
            color: {palette['text']};
            border: 1px solid {palette['border']};
        }}
        QMenu::item {{ padding: 6px 24px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {palette['accent2']}; color: {highlight_text}; }}
        QDialog, QMessageBox {{
            background: {palette['panel']};
            color: {palette['text']};
        }}
        QDialog QLabel, QMessageBox QLabel {{ color: {palette['text']}; }}
        QDialog QPushButton, QMessageBox QPushButton {{
            padding: 8px 14px;
            border-radius: 8px;
        }}
        QToolTip {{
            background: {palette['panel']};
            color: {palette['text']};
            border: 1px solid {palette['border']};
            padding: 6px 8px;
        }}
        #Footer {{ color: {palette['sub']}; font-size: 12px; padding: 8px 0; }}
        #WarnLabel {{ color: {palette['warn']}; font-size: 12px; }}
        #LinkButton {{
            background: transparent;
            color: {palette['accent']};
            border: none;
            text-decoration: underline;
            padding: 0px;
            font-weight: 600;
        }}
        #LinkButton:hover {{ color: {palette['accent2']}; }}
        #LinkButton:pressed {{ color: {palette['accent']}; opacity: 0.8; }}
        #LinkButton:disabled {{ color: {palette['muted']}; }}
    """
