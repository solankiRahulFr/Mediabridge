from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QPointF, QEvent, QUrl
from PySide6.QtGui import QTouchEvent
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QVBoxLayout, QWidget

log = logging.getLogger(__name__)

_MIN_ZOOM = 0.25
_MAX_ZOOM = 5.0


class TouchPDFViewer(QWidget):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._doc = QPdfDocument(self)
        self._view = QPdfView(self)
        self._view.setDocument(self._doc)
        self._view.setPageMode(QPdfView.PageMode.SinglePage)
        self._view.setZoomMode(QPdfView.ZoomMode.FitInView)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._view)

        # Touch state
        self._pinch_active = False
        self._initial_distance = 0.0
        self._pinch_start_zoom = 1.0

        self._dragging = False
        self._last_pos = QPointF()

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self._view.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self._view.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        self._view.installEventFilter(self)
        self._view.viewport().installEventFilter(self)

    # ── Public API ────────────────────────────────────────────────

    @property
    def document(self) -> QPdfDocument:
        return self._doc

    @property
    def view(self) -> QPdfView:
        return self._view

    def load(self, path_or_url: str) -> None:
        if path_or_url.startswith("http"):
            self._doc.load(QUrl(path_or_url))
        else:
            self._doc.load(path_or_url)

    def close_doc(self) -> None:
        self._doc.close()

    def page_count(self) -> int:
        return self._doc.pageCount()

    def current_page(self) -> int:
        return self._view.pageNavigator().currentPage()

    def go_to_page(self, page: int) -> None:
        page = max(0, min(page, self._doc.pageCount() - 1))
        nav = self._view.pageNavigator()
        nav.jump(page, QUrl(), 0)

    def next_page(self) -> None:
        self.go_to_page(self.current_page() + 1)

    def prev_page(self) -> None:
        self.go_to_page(self.current_page() - 1)

    def zoom_in(self) -> None:
        self._set_zoom(self._view.zoomFactor() * 1.25)

    def zoom_out(self) -> None:
        self._set_zoom(self._view.zoomFactor() / 1.25)

    def zoom_reset(self) -> None:
        self._view.setZoomMode(QPdfView.ZoomMode.FitInView)

    def _set_zoom(self, factor: float) -> None:
        factor = max(_MIN_ZOOM, min(_MAX_ZOOM, factor))
        self._view.setZoomMode(QPdfView.ZoomMode.Custom)
        self._view.setZoomFactor(factor)

    # ── Event filter for touch on viewport ────────────────────────

    def eventFilter(self, obj, event: QEvent) -> bool:
        t = event.type()
        if t == QEvent.TouchBegin:
            self._on_touch_begin(event)
            return True
        elif t == QEvent.TouchUpdate:
            self._on_touch_update(event)
            return True
        elif t == QEvent.TouchEnd:
            self._on_touch_end(event)
            return True
        return super().eventFilter(obj, event)

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
            pos = points[0].position()
            dy = pos.y() - self._last_pos.y()
            # Scroll the PDF view
            vbar = self._view.verticalScrollBar()
            if vbar:
                vbar.setValue(int(vbar.value() - dy))
            hbar = self._view.horizontalScrollBar()
            dx = pos.x() - self._last_pos.x()
            if hbar:
                hbar.setValue(int(hbar.value() - dx))
            self._last_pos = pos
        event.accept()

    def _on_touch_end(self, event: QTouchEvent) -> None:
        self._dragging = False
        self._pinch_active = False
        event.accept()

    def _start_pinch(self, points) -> None:
        p0 = points[0].position()
        p1 = points[1].position()
        self._initial_distance = self._touch_distance(p0, p1)
        self._pinch_start_zoom = self._view.zoomFactor()
        self._pinch_active = True

    def _update_pinch(self, points) -> None:
        p0 = points[0].position()
        p1 = points[1].position()
        dist = self._touch_distance(p0, p1)
        if self._initial_distance < 1:
            return
        factor = dist / self._initial_distance
        new_zoom = max(_MIN_ZOOM, min(_MAX_ZOOM, self._pinch_start_zoom * factor))
        self._view.setZoomMode(QPdfView.ZoomMode.Custom)
        self._view.setZoomFactor(new_zoom)

    @staticmethod
    def _touch_distance(p0: QPointF, p1: QPointF) -> float:
        d = p1 - p0
        return (d.x() ** 2 + d.y() ** 2) ** 0.5
