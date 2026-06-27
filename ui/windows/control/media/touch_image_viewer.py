
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QUrl
from PySide6.QtGui import (
    QPixmap, QPainter, QTransform, QWheelEvent,
    QMouseEvent, QTouchEvent,
)
from PySide6.QtWidgets import QWidget, QGestureEvent
from PySide6.QtCore import QEvent

log = logging.getLogger(__name__)

_MIN_SCALE = 0.2
_MAX_SCALE = 8.0


class TouchImageViewer(QWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self._scale: float = 1.0
        self._offset = QPointF(0, 0)

        # Drag state
        self._dragging = False
        self._last_pos = QPointF()

        # Pinch state
        self._pinch_active = False
        self._pinch_start_scale = 1.0
        self._pinch_center = QPointF()
        self._initial_distance = 0.0

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setStyleSheet("background: #000;")
        self.setMouseTracking(True)

    # ── Public API ────────────────────────────────────────────────

    def load(self, path_or_url: str) -> None:
        px = QPixmap(path_or_url)
        if px.isNull():
            log.warning("Cannot load image: %s", path_or_url)
            return
        self._pixmap = px
        self._fit()
        self.update()

    def clear(self) -> None:
        self._pixmap = None
        self._scale = 1.0
        self._offset = QPointF(0, 0)
        self.update()

    def zoom_in(self) -> None:
        self._zoom_by(1.25)

    def zoom_out(self) -> None:
        self._zoom_by(1.0 / 1.25)

    def zoom_reset(self) -> None:
        self._fit()
        self.update()

    # ── Painting ──────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        if not self._pixmap:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.translate(self._offset)
        p.scale(self._scale, self._scale)
        p.drawPixmap(0, 0, self._pixmap)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._pixmap:
            self._fit()

    # ── Fit / zoom helpers ────────────────────────────────────────

    def _fit(self) -> None:
        if not self._pixmap:
            return
        pw, ph = self._pixmap.width(), self._pixmap.height()
        vw, vh = self.width() or 1, self.height() or 1
        sx = vw / pw
        sy = vh / ph
        self._scale = min(sx, sy)
        # Centre the image
        sw = pw * self._scale
        sh = ph * self._scale
        self._offset = QPointF((vw - sw) / 2, (vh - sh) / 2)
        self.update()

    def _zoom_by(self, factor: float, center: QPointF | None = None) -> None:
        new_scale = max(_MIN_SCALE, min(_MAX_SCALE, self._scale * factor))
        if center is None:
            center = QPointF(self.width() / 2, self.height() / 2)
        # Zoom around center point
        old_pos = (center - self._offset) / self._scale
        self._scale = new_scale
        self._offset = center - old_pos * self._scale
        self._clamp_offset()
        self.update()

    def _clamp_offset(self) -> None:
        if not self._pixmap:
            return
        sw = self._pixmap.width() * self._scale
        sh = self._pixmap.height() * self._scale
        vw, vh = self.width(), self.height()
        # Allow panning only if image is larger than view
        if sw <= vw:
            self._offset.setX((vw - sw) / 2)
        else:
            max_x = 0.0
            min_x = vw - sw
            self._offset.setX(max(min_x, min(max_x, self._offset.x())))
        if sh <= vh:
            self._offset.setY((vh - sh) / 2)
        else:
            max_y = 0.0
            min_y = vh - sh
            self._offset.setY(max(min_y, min(max_y, self._offset.y())))

    # ── Mouse events (single-finger drag / desktop) ───────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_pos = event.position()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            delta = event.position() - self._last_pos
            self._offset += delta
            self._last_pos = event.position()
            self._clamp_offset()
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._fit()
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self._zoom_by(factor, event.position())
        event.accept()

    # ── Touch events (pinch-to-zoom) ──────────────────────────────

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.TouchBegin:
            self._on_touch_begin(event)
            return True
        elif event.type() == QEvent.TouchUpdate:
            self._on_touch_update(event)
            return True
        elif event.type() == QEvent.TouchEnd:
            self._on_touch_end(event)
            return True
        return super().event(event)

    def _on_touch_begin(self, event: QTouchEvent) -> None:
        points = event.points()
        if len(points) == 2:
            self._start_pinch(points)
        elif len(points) == 1:
            self._dragging = True
            self._last_pos = points[0].position()
        event.accept()

    def _on_touch_update(self, event: QTouchEvent) -> None:
        points = event.points()
        if len(points) >= 2:
            if not self._pinch_active:
                self._start_pinch(points[:2])
            self._update_pinch(points[:2])
        elif len(points) == 1 and self._dragging and not self._pinch_active:
            delta = points[0].position() - self._last_pos
            self._offset += delta
            self._last_pos = points[0].position()
            self._clamp_offset()
            self.update()
        event.accept()

    def _on_touch_end(self, event: QTouchEvent) -> None:
        self._dragging = False
        self._pinch_active = False
        event.accept()

    def _start_pinch(self, points) -> None:
        p0 = points[0].position()
        p1 = points[1].position()
        self._initial_distance = self._touch_distance(p0, p1)
        self._pinch_start_scale = self._scale
        self._pinch_center = (p0 + p1) / 2
        self._pinch_active = True

    def _update_pinch(self, points) -> None:
        p0 = points[0].position()
        p1 = points[1].position()
        dist = self._touch_distance(p0, p1)
        if self._initial_distance < 1:
            return
        factor = dist / self._initial_distance
        new_scale = max(_MIN_SCALE, min(_MAX_SCALE, self._pinch_start_scale * factor))
        center = (p0 + p1) / 2
        old_pos = (self._pinch_center - self._offset) / self._scale
        self._scale = new_scale
        self._offset = center - old_pos * self._scale
        self._pinch_center = center
        self._clamp_offset()
        self.update()

    @staticmethod
    def _touch_distance(p0: QPointF, p1: QPointF) -> float:
        d = p1 - p0
        return (d.x() ** 2 + d.y() ** 2) ** 0.5
