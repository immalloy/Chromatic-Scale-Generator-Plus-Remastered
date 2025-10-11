from __future__ import annotations

"""Application entry point."""

import os
import sys

from PySide6.QtCore import QLocale, QPoint, QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QSplashScreen

from i18n_pkg import T, list_languages

from .constants import APP_ICON_PATH, SPLASH_SIZE
from .main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    splash_lang = _detect_initial_language()
    splash_pixmap = _build_splash_pixmap(
        SPLASH_SIZE,
        APP_ICON_PATH,
        T(splash_lang, "SplashTitle"),
        T(splash_lang, "SplashSubtitle"),
        T(splash_lang, "SplashCredits"),
    )
    splash = QSplashScreen(splash_pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    try:
        if os.path.exists(APP_ICON_PATH):
            app.setWindowIcon(QIcon(APP_ICON_PATH))
    except Exception:  # pragma: no cover - environment specific
        pass

    window = MainWindow()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())


def _detect_initial_language() -> str:
    """Return the best-fit language for the splash screen."""

    available = {code for code, _ in list_languages()}
    locale = QLocale.system().name().split("_")[0]
    if locale in available:
        return locale
    return "en"


def _build_splash_pixmap(
    size: QSize, icon_path: str, title: str, subtitle: str, credits: str
) -> QPixmap:
    """Create a stylised pixmap used by the splash screen."""

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    gradient = QLinearGradient(0, 0, size.width(), size.height())
    gradient.setColorAt(0.0, QColor(28, 14, 54))
    gradient.setColorAt(0.4, QColor(58, 22, 90))
    gradient.setColorAt(1.0, QColor(120, 54, 146))
    painter.fillRect(pixmap.rect(), gradient)

    margin = 96

    painter.save()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(255, 255, 255, 28))
    painter.drawEllipse(
        int(size.width() * 0.55),
        -int(size.height() * 0.25),
        int(size.width() * 0.9),
        int(size.height() * 0.9),
    )
    painter.setBrush(QColor(249, 121, 198, 45))
    painter.drawEllipse(
        -int(size.width() * 0.2),
        int(size.height() * 0.55),
        int(size.width() * 0.7),
        int(size.height() * 0.7),
    )
    painter.restore()

    painter.save()
    painter.setPen(
        QPen(QColor(255, 255, 255, 90), 12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    )
    stroke = QPainterPath()
    stroke.moveTo(margin, size.height() * 0.68)
    stroke.cubicTo(
        size.width() * 0.28,
        size.height() * 0.52,
        size.width() * 0.52,
        size.height() * 0.88,
        size.width() * 0.78,
        size.height() * 0.72,
    )
    painter.drawPath(stroke)

    painter.setPen(
        QPen(QColor(255, 168, 225, 110), 20, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    )
    highlight = QPainterPath()
    highlight.moveTo(size.width() * 0.18, size.height() * 0.85)
    highlight.cubicTo(
        size.width() * 0.34,
        size.height() * 0.95,
        size.width() * 0.58,
        size.height() * 0.95,
        size.width() * 0.82,
        size.height() * 0.82,
    )
    painter.drawPath(highlight)
    painter.restore()

    panel_width = int(size.width() * 0.58)
    panel_height = int(size.height() * 0.32)
    panel_rect = QRect(margin, margin, panel_width, panel_height)

    painter.save()
    painter.setPen(QColor(255, 255, 255, 40))
    painter.setBrush(QColor(18, 10, 36, 180))
    painter.drawRoundedRect(panel_rect, 48, 48)
    painter.restore()

    icon_left = panel_rect.left() + 64
    icon_top = panel_rect.top() + 64
    icon_max = panel_rect.height() - 128

    icon = QPixmap(icon_path)
    if not icon.isNull():
        target = icon.scaled(
            icon_max,
            icon_max,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        icon_pos = QPoint(icon_left, icon_top + (icon_max - target.height()) // 2)
        painter.drawPixmap(icon_pos, target)
        text_left = icon_pos.x() + target.width() + 48
    else:
        text_left = panel_rect.left() + 64

    text_width = panel_rect.right() - text_left - 64

    title_font = QFont()
    title_font.setPointSize(64)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(QColor("#FFFFFF"))
    title_rect = QRect(
        text_left,
        panel_rect.top() + 48,
        text_width,
        panel_rect.height() // 2,
    )
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, title)

    subtitle_font = QFont()
    subtitle_font.setPointSize(28)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#D8D5FF"))
    subtitle_rect = QRect(
        text_left,
        panel_rect.top() + panel_rect.height() // 2,
        text_width,
        panel_rect.height() // 2 - 48,
    )
    painter.drawText(
        subtitle_rect,
        Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        subtitle,
    )

    credit_width = int(size.width() * 0.3)
    credits_panel_rect = QRect(
        size.width() - credit_width - margin,
        margin,
        credit_width,
        int(panel_height * 0.85),
    )

    painter.save()
    painter.setPen(QColor(255, 255, 255, 35))
    painter.setBrush(QColor(36, 18, 64, 170))
    painter.drawRoundedRect(credits_panel_rect, 36, 36)
    painter.restore()

    credits_font = QFont()
    credits_font.setPointSize(28)
    credits_font.setItalic(True)
    painter.setFont(credits_font)
    painter.setPen(QColor(240, 226, 255))
    credits_rect = credits_panel_rect.adjusted(32, 32, -32, -32)
    painter.drawText(
        credits_rect,
        Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap,
        credits,
    )

    painter.end()
    return pixmap


__all__ = ["main"]
