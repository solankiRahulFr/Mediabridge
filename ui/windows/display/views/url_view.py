
from __future__ import annotations
import logging

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QVBoxLayout, QWidget

log = logging.getLogger("mediabridge.display.url")

# QWebEngineView is optional — not every dev machine has it installed
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEB = True
except ImportError:
    _HAS_WEB = False
    log.warning("PySide6-WebEngine not found — URL view will show a placeholder")


class URLView(QWidget):
    def __init__(self, url: str, refresh_minutes: float = 0.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._url = url
        self._refresh_minutes = refresh_minutes
        self._timer: QTimer | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _HAS_WEB:
            self._web = QWebEngineView()
            layout.addWidget(self._web)
        else:
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt
            lbl = QLabel(f"⚠  QWebEngineView unavailable\n\nURL: {url}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#8B90A8; font-size:16px;")
            layout.addWidget(lbl)
            self._web = None

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        """Load the URL and arm the refresh timer."""
        self._load()
        if self._refresh_minutes > 0 and self._web:
            interval_ms = int(self._refresh_minutes * 60 * 1000)
            self._timer = QTimer(self)
            self._timer.setInterval(interval_ms)
            self._timer.timeout.connect(self._load)
            self._timer.start()
            log.info("URL auto-refresh every %.1f min", self._refresh_minutes)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
        if self._web:
            self._web.setUrl(QUrl("about:blank"))

    # ── Internals ────────────────────────────────────────────────────────────
    def _load(self) -> None:
        if self._web:
            log.debug("Loading URL: %s", self._url)
            self._web.setUrl(QUrl(self._url))

    def set_url(self, url: str) -> None:
        self._url = url
        self._load()
