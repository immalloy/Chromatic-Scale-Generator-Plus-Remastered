from __future__ import annotations

"""Application entry point."""

import os
import sys

from PySide6.QtCore import QElapsedTimer, QLocale, QPoint, QRect, QSize, Qt, QThread
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

from .constants import (
    APP_ICON_PATH,
    SPLASH_ART_PATH,
    SPLASH_MIN_DURATION_MS,
    SPLASH_SIZE,
)
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
        SPLASH_ART_PATH,
    )
    splash = QSplashScreen(splash_pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint)
    splash.show()
    splash_timer = QElapsedTimer()
    splash_timer.start()
    app.processEvents()

    try:
        if os.path.exists(APP_ICON_PATH):
            app.setWindowIcon(QIcon(APP_ICON_PATH))
    except Exception:  # pragma: no cover - environment specific
        pass

    window = MainWindow()
    window.show()
    _enforce_minimum_splash_duration(app, splash_timer, SPLASH_MIN_DURATION_MS)
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
    size: QSize,
    icon_path: str,
    title: str,
    subtitle: str,
    credits: str,
    art_path: str | None,
) -> QPixmap:
    """Create a stylised pixmap used by the splash screen."""

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    art = QPixmap(art_path) if art_path else QPixmap()
    if not art.isNull():
        scaled = art.scaled(
            size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        source_width = min(size.width(), scaled.width())
        source_height = min(size.height(), scaled.height())
        source = QRect(
            max(0, (scaled.width() - source_width) // 2),
            max(0, (scaled.height() - source_height) // 2),
            source_width,
            source_height,
        )
        target_rect = QRect(0, 0, source_width, source_height)
        target_rect.moveCenter(pixmap.rect().center())
        painter.drawPixmap(target_rect, scaled, source)
        painter.fillRect(pixmap.rect(), QColor(20, 10, 38, 160))
    else:
        gradient = QLinearGradient(0, 0, size.width(), size.height())
        gradient.setColorAt(0.0, QColor(28, 14, 54))
        gradient.setColorAt(0.4, QColor(58, 22, 90))
        gradient.setColorAt(1.0, QColor(120, 54, 146))
        painter.fillRect(pixmap.rect(), gradient)

    margin = int(size.width() * 0.055)

    painter.save()
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(255, 255, 255, 28))
    painter.drawEllipse(
        int(size.width() * 0.55),
        -int(size.height() * 0.25),
        int(size.width() * 0.78),
        int(size.height() * 0.78),
    )
    painter.setBrush(QColor(249, 121, 198, 45))
    painter.drawEllipse(
        -int(size.width() * 0.2),
        int(size.height() * 0.55),
        int(size.width() * 0.58),
        int(size.height() * 0.58),
    )
    painter.restore()

    painter.save()
    painter.setPen(
        QPen(QColor(255, 255, 255, 90), 12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    )
    stroke = QPainterPath()
    stroke.moveTo(margin, size.height() * 0.68)
    stroke.cubicTo(
        size.width() * 0.22,
        size.height() * 0.52,
        size.width() * 0.5,
        size.height() * 0.82,
        size.width() * 0.74,
        size.height() * 0.68,
    )
    painter.drawPath(stroke)

    painter.setPen(
        QPen(QColor(255, 168, 225, 110), 20, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    )
    highlight = QPainterPath()
    highlight.moveTo(size.width() * 0.18, size.height() * 0.85)
    highlight.cubicTo(
        size.width() * 0.3,
        size.height() * 0.9,
        size.width() * 0.54,
        size.height() * 0.94,
        size.width() * 0.78,
        size.height() * 0.8,
    )
    painter.drawPath(highlight)
    painter.restore()

    panel_width = int(size.width() * 0.48)
    panel_height = int(size.height() * 0.36)
    panel_rect = QRect(margin, int(size.height() * 0.16), panel_width, panel_height)

    painter.save()
    painter.setPen(QColor(255, 255, 255, 50))
    painter.setBrush(QColor(14, 8, 28, 200))
    painter.drawRoundedRect(panel_rect, 26, 26)
    painter.restore()

    icon_left = panel_rect.left() + 36
    icon_top = panel_rect.top() + 40
    icon_max = min(panel_rect.height() - 96, panel_rect.width() // 5)

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
        text_left = icon_pos.x() + target.width() + 32
    else:
        text_left = panel_rect.left() + 40

    text_width = panel_rect.right() - text_left - 36

    title_font = QFont()
    title_font.setPointSizeF(size.height() * 0.045)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(QColor("#FFFFFF"))
    title_rect = QRect(
        text_left,
        panel_rect.top() + 28,
        text_width,
        int(panel_rect.height() * 0.5),
    )
    painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, title)

    subtitle_font = QFont()
    subtitle_font.setPointSizeF(size.height() * 0.024)
    painter.setFont(subtitle_font)
    painter.setPen(QColor("#D8D5FF"))
    subtitle_rect = QRect(
        text_left,
        title_rect.bottom() + 10,
        text_width,
        panel_rect.bottom() - (title_rect.bottom() + 28),
    )
    painter.drawText(
        subtitle_rect,
        Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        subtitle,
    )

    credit_width = int(size.width() * 0.26)
    credits_panel_rect = QRect(
        size.width() - credit_width - margin,
        int(size.height() * 0.16),
        credit_width,
        int(panel_height * 0.62),
    )

    painter.save()
    painter.setPen(QColor(255, 255, 255, 30))
    painter.setBrush(QColor(36, 18, 64, 160))
    painter.drawRoundedRect(credits_panel_rect, 28, 28)
    painter.restore()

    credits_font = QFont()
    credits_font.setPointSizeF(size.height() * 0.022)
    credits_font.setItalic(True)
    painter.setFont(credits_font)
    painter.setPen(QColor(240, 226, 255))
    credits_rect = credits_panel_rect.adjusted(28, 28, -28, -28)
    painter.drawText(
        credits_rect,
        Qt.AlignRight | Qt.AlignTop | Qt.TextWordWrap,
        credits,
    )

    painter.end()
    return pixmap


def _enforce_minimum_splash_duration(
    app: QApplication, timer: QElapsedTimer, minimum_ms: int
) -> None:
    """Block the main thread until the splash has been visible long enough."""

    if minimum_ms <= 0:
        return

    while timer.elapsed() < minimum_ms:
        app.processEvents()
        remaining = minimum_ms - timer.elapsed()
        QThread.msleep(min(remaining, 50))


__all__ = ["main"]
