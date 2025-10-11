from __future__ import annotations

"""Qt stylesheet helpers."""

from typing import Dict, Tuple

PaletteKey = Tuple[str, str]
Palette = Dict[str, str]


_BASE_DARK: Palette = dict(
    bg="#15171D",
    panel="#1C1F27",
    text="#EFF2FA",
    sub="#BBC3D8",
    field="#242832",
    border="#303645",
    warn="#FFB3B3",
    muted="#8F97AA",
)

_ACCENTS: dict[str, Palette] = {
    "blue": dict(
        accent="#2D7CF3",
        accent_hover="#4D90FE",
        accent_active="#1F5FCC",
        accent_soft="#2A364F",
        accent_outline="#7EB0FF",
        on_accent="#F7FAFF",
    ),
    "pink": dict(
        accent="#FF5AA1",
        accent_hover="#FF7FBF",
        accent_active="#E44B90",
        accent_soft="#3A2635",
        accent_outline="#FF9BC5",
        on_accent="#FFF5FA",
    ),
    "green": dict(
        accent="#42C67D",
        accent_hover="#5FDA95",
        accent_active="#32A566",
        accent_soft="#243830",
        accent_outline="#8ADFB4",
        on_accent="#F4FFF9",
    ),
}


def _build_palette(accent: str) -> Palette:
    palette = dict(_BASE_DARK)
    palette.update(_ACCENTS[accent])
    return palette


PALETTES: dict[PaletteKey, Palette] = {
    ("dark", accent): _build_palette(accent) for accent in _ACCENTS
}


def _encode_color(color: str) -> str:
    """Return a hex colour suitable for embedding in data URIs."""

    return color.replace("#", "%23")


def build_stylesheet(mode: str, accent: str) -> str:
    key = (mode, accent)
    if key not in PALETTES:
        key = ("dark", "pink")
    palette = PALETTES[key]
    highlight_text = palette["on_accent"]
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
    check_mark = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12' viewBox='0 0 16 12'>"
        f"<path fill='{_encode_color(palette['on_accent'])}' d='M6.2 11.2L0.8 6.0L2.7 4.1L6.1 7.3L13.0 0.8L15.2 3.0Z'/>"
        "</svg>"
    )
    check_mark_disabled = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12' viewBox='0 0 16 12'>"
        f"<path fill='{_encode_color(palette['muted'])}' d='M6.2 11.2L0.8 6.0L2.7 4.1L6.1 7.3L13.0 0.8L15.2 3.0Z'/>"
        "</svg>"
    )
    minus_mark = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12' viewBox='0 0 16 12'>"
        f"<rect fill='{_encode_color(palette['on_accent'])}' x='2' y='5' width='12' height='2' rx='1'/>"
        "</svg>"
    )
    minus_mark_disabled = (
        "data:image/svg+xml;utf8," +
        f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12' viewBox='0 0 16 12'>"
        f"<rect fill='{_encode_color(palette['muted'])}' x='2' y='5' width='12' height='2' rx='1'/>"
        "</svg>"
    )
    return f"""
        QMainWindow {{ background: {palette['bg']}; }}
        QWidget {{
            background-color: {palette['bg']};
            color: {palette['text']};
        }}
        QGroupBox {{
            color: {palette['text']};
            border: 1px solid {palette['border']};
            border-radius: 12px;
            margin-top: 12px;
            padding-top: 14px;
            background: {palette['panel']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
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
            selection-background-color: {palette['accent_hover']};
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
            background: {palette['panel']};
        }}
        QComboBox QAbstractItemView {{
            background: {palette['panel']};
            border: 1px solid {palette['border']};
            color: {palette['text']};
            selection-background-color: {palette['accent_hover']};
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
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 10px 16px;
            color: {palette['on_accent']};
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {palette['accent_hover']}; }}
        QPushButton:pressed {{ background: {palette['accent_active']}; }}
        QPushButton:focus {{
            outline: none;
            border: 1px solid {palette['accent_outline']};
        }}
        QPushButton:disabled {{
            background: {palette['border']};
            color: {palette['muted']};
            border: 1px solid {palette['border']};
        }}
        QPushButton#CancelButton {{
            background: {palette['border']};
            color: {palette['muted']};
            border: 1px solid {palette['border']};
        }}
        QPushButton#CancelButton:enabled {{
            background: {palette['accent_soft']};
            color: {highlight_text};
            border: 1px solid {palette['accent']};
        }}
        QPushButton#CancelButton:enabled:hover {{
            background: {palette['accent']};
            border-color: {palette['accent']};
        }}
        QPushButton#CancelButton:enabled:pressed {{
            background: {palette['accent_active']};
            border-color: {palette['accent_active']};
        }}
        QPushButton#OpenOutputButton {{
            background: {palette['border']};
            color: {palette['muted']};
            border: 1px solid {palette['border']};
        }}
        QPushButton#OpenOutputButton:enabled {{
            background: {palette['accent_soft']};
            color: {highlight_text};
            border: 1px solid {palette['accent_outline']};
        }}
        QPushButton#OpenOutputButton:enabled:hover {{
            background: {palette['accent']};
            border-color: {palette['accent']};
        }}
        QPushButton#OpenOutputButton:enabled:pressed {{
            background: {palette['accent_active']};
            border-color: {palette['accent_active']};
        }}
        QProgressBar {{
            background: {palette['field']};
            border: 1px solid {palette['border']};
            border-radius: 8px;
            text-align: center;
            color: {palette['text']};
            height: 18px;
        }}
        QProgressBar::chunk {{
            border-radius: 7px;
            margin: 1px;
            background: {palette['accent']};
        }}
        QSlider::groove:horizontal {{
            border: 1px solid {palette['border']};
            height: 6px;
            border-radius: 3px;
            background: {palette['field']};
        }}
        QSlider::groove:vertical {{
            border: 1px solid {palette['border']};
            width: 6px;
            border-radius: 3px;
            background: {palette['field']};
        }}
        QSlider::handle:horizontal {{
            background: {palette['accent']};
            border: 2px solid {palette['accent_outline']};
            width: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{ background: {palette['accent_hover']}; }}
        QSlider::handle:horizontal:pressed {{ background: {palette['accent_active']}; }}
        QSlider::handle:vertical {{
            background: {palette['accent']};
            border: 2px solid {palette['accent_outline']};
            height: 16px;
            margin: 0 -6px;
            border-radius: 8px;
        }}
        QSlider::handle:vertical:hover {{ background: {palette['accent_hover']}; }}
        QSlider::handle:vertical:pressed {{ background: {palette['accent_active']}; }}
        QScrollBar:vertical {{
            background: {palette['panel']};
            width: 12px;
            margin: 4px 0 4px 0;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {palette['border']};
            border-radius: 6px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {palette['accent_soft']}; }}
        QScrollBar::handle:vertical:pressed {{ background: {palette['accent']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {palette['panel']};
            height: 12px;
            margin: 0 4px 0 4px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {palette['border']};
            border-radius: 6px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {palette['accent_soft']}; }}
        QScrollBar::handle:horizontal:pressed {{ background: {palette['accent']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
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
        QMenuBar::item:selected {{ background: {palette['accent_soft']}; color: {highlight_text}; }}
        QMenu {{
            background: {palette['panel']};
            color: {palette['text']};
            border: 1px solid {palette['border']};
        }}
        QMenu::item {{ padding: 6px 24px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {palette['accent_soft']}; color: {highlight_text}; }}
        QDialog, QMessageBox {{
            background: {palette['panel']};
            color: {palette['text']};
        }}
        QDialog QLabel, QMessageBox QLabel {{ color: {palette['text']}; }}
        QDialog QPushButton, QMessageBox QPushButton {{
            padding: 8px 14px;
            border-radius: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid {palette['border']};
            background: {palette['field']};
        }}
        QCheckBox::indicator:hover {{ border: 1px solid {palette['accent_hover']}; }}
        QCheckBox::indicator:checked {{
            border: 1px solid {palette['accent']};
            background: {palette['accent']};
            image: url({check_mark});
        }}
        QCheckBox::indicator:checked:hover {{
            border: 1px solid {palette['accent_hover']};
            background: {palette['accent_hover']};
        }}
        QCheckBox::indicator:checked:disabled {{
            border: 1px solid {palette['border']};
            background: {palette['border']};
            image: url({check_mark_disabled});
        }}
        QCheckBox::indicator:disabled {{
            border: 1px solid {palette['border']};
            background: {palette['panel']};
        }}
        QCheckBox::indicator:indeterminate {{
            border: 1px solid {palette['accent']};
            background: {palette['accent']};
            image: url({minus_mark});
        }}
        QCheckBox::indicator:indeterminate:disabled {{
            border: 1px solid {palette['border']};
            background: {palette['border']};
            image: url({minus_mark_disabled});
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
        #LinkButton:hover {{ color: {palette['accent_hover']}; }}
        #LinkButton:pressed {{ color: {palette['accent_active']}; }}
        #LinkButton:disabled {{ color: {palette['muted']}; }}
    """
