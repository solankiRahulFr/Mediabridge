
from __future__ import annotations
import logging
from pathlib import Path
from typing import Literal

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QWidget, QLabel, QStackedLayout

log = logging.getLogger("mediabridge.display.image")


class _FadeLabel(QLabel):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._opacity: float = 1.0

    # ── Custom paint so we can honour opacity ─────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: ANN001
        if self._opacity >= 1.0:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(0, 0, self._scaled_px)


class ImageCarouselView(QWidget):
    def __init__(
        self,
        image_paths: list[str],
        interval_seconds: int = 10,
        screensaver_mode: bool = False,
        fit: Literal["fill", "contain", "stretch"] = "contain",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._paths = [p for p in image_paths if Path(p).is_file()]
        self._interval = interval_seconds
        self._screensaver = screensaver_mode
        self._fit = fit
        self._index = 0
        self._timer: QTimer | None = None

        self.setStyleSheet("background: #000000;")

        # Two labels for cross-fade
        self._labels: list[QLabel] = []
        for _ in range(2):
            lbl = QLabel(self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background: transparent;")
            lbl.setGeometry(self.rect())
            self._labels.append(lbl)

        self._front = 0  # which label is currently visible

        if not self._paths:
            self._show_placeholder()

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        if not self._paths:
            return
        self._show_index(0)
        if not self._screensaver and len(self._paths) > 1:
            self._timer = QTimer(self)
            self._timer.setInterval(self._interval * 1000)
            self._timer.timeout.connect(self._advance)
            self._timer.start()
            log.info("Image carousel started — %d images, %ds interval",
                     len(self._paths), self._interval)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()

    # ── Resize handling ───────────────────────────────────────────────────────
    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        for lbl in self._labels:
            lbl.setGeometry(self.rect())
        # Redraw current image at new size
        if self._paths:
            self._show_index(self._index, fade=False)

    # ── Internals ─────────────────────────────────────────────────────────────
    def _advance(self) -> None:
        self._index = (self._index + 1) % len(self._paths)
        self._show_index(self._index)

    def _show_index(self, idx: int, fade: bool = True) -> None:
        path = self._paths[idx]
        px = QPixmap(path)
        if px.isNull():
            log.warning("Cannot load image: %s", path)
            return

        scaled = self._scale_pixmap(px)

        back = 1 - self._front
        self._labels[back].setPixmap(scaled)
        self._labels[back].raise_()

        if fade:
            # Fade the back label in over 800 ms via window opacity trick
            eff_widget = self._labels[back]
            anim = QPropertyAnimation(eff_widget, b"windowOpacity", self)
            anim.setDuration(800)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.InOutCubic)

            # Hide old front after fade
            old_front_lbl = self._labels[self._front]
            anim.finished.connect(lambda: old_front_lbl.lower())
            anim.start()
        else:
            self._labels[back].raise_()
            self._labels[self._front].lower()

        self._front = back

    def _scale_pixmap(self, px: QPixmap) -> QPixmap:
        w, h = self.width() or 1920, self.height() or 1080
        if self._fit == "contain":
            return px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif self._fit == "fill":
            return px.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        else:  # stretch
            return px.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def _show_placeholder(self) -> None:
        lbl = QLabel("No images found\nDrop images into the config to get started",
                      self)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #5C6080; font-size: 18px;")
        lbl.setGeometry(self.rect())
        lbl.show()
