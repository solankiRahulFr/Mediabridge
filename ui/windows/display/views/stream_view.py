
from __future__ import annotations
import logging
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

log = logging.getLogger("mediabridge.display.stream")

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    _HAS_WEB = True
except ImportError:
    _HAS_WEB = False
    log.warning("PySide6-WebEngine not found — stream view unavailable")


def _to_embed_url(raw: str, autoplay: bool, loop: bool, muted: bool) -> str:

    # ── YouTube ───────────────────────────────────────────────────────────────
    yt_watch = re.match(
        r"https?://(?:www\.)?youtube\.com/watch\?.*v=([A-Za-z0-9_\-]{11})", raw
    )
    yt_short = re.match(
        r"https?://youtu\.be/([A-Za-z0-9_\-]{11})", raw
    )
    yt_embed = re.match(
        r"https?://(?:www\.)?youtube\.com/embed/([A-Za-z0-9_\-]{11})", raw
    )

    vid_id = None
    if yt_watch:
        vid_id = yt_watch.group(1)
    elif yt_short:
        vid_id = yt_short.group(1)
    elif yt_embed:
        vid_id = yt_embed.group(1)

    if vid_id:
        params = {
            "autoplay": "1" if autoplay else "0",
            "mute":     "1" if muted else "0",
            "loop":     "1" if loop else "0",
            "playlist": vid_id,          # required for loop to work
            "controls": "0",
            "rel":      "0",
            "modestbranding": "1",
        }
        return f"https://www.youtube.com/embed/{vid_id}?{urlencode(params)}"

    # ── Vimeo ─────────────────────────────────────────────────────────────────
    vimeo = re.match(r"https?://(?:www\.)?vimeo\.com/(\d+)", raw)
    if vimeo:
        vid_id = vimeo.group(1)
        params = {
            "autoplay": "1" if autoplay else "0",
            "muted":    "1" if muted else "0",
            "loop":     "1" if loop else "0",
            "title":    "0",
            "byline":   "0",
            "portrait": "0",
        }
        return f"https://player.vimeo.com/video/{vid_id}?{urlencode(params)}"

    # ── Fallback — use as-is ──────────────────────────────────────────────────
    log.debug("StreamView: using URL as-is (no rewrite rule matched): %s", raw)
    return raw


class StreamView(QWidget):
    def __init__(
        self,
        stream_url: str,
        autoplay: bool = True,
        loop: bool = True,
        muted: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._raw_url = stream_url
        self._autoplay = autoplay
        self._loop = loop
        self._muted = muted

        self.setStyleSheet("background: #000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _HAS_WEB:
            self._web = QWebEngineView(self)
            # Allow autoplay without user gesture
            settings = self._web.settings()
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False
            )
            layout.addWidget(self._web)
        else:
            lbl = QLabel(
                "⚠  QWebEngineView unavailable\n\n"
                "Install PySide6-Addons to use stream / YouTube mode.\n\n"
                f"URL: {stream_url}",
                self,
            )
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #8B90A8; font-size: 16px;")
            layout.addWidget(lbl)
            self._web = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self) -> None:
        if not self._web:
            return
        embed = _to_embed_url(self._raw_url, self._autoplay, self._loop, self._muted)
        log.info("StreamView loading: %s", embed)
        self._web.setUrl(QUrl(embed))

    def stop(self) -> None:
        if self._web:
            self._web.setUrl(QUrl("about:blank"))