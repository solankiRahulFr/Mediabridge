
from __future__ import annotations
import logging

from PySide6.QtCore import Qt, QEvent, QObject, QRect, QTimer, QPoint
from PySide6.QtGui import (
    QAction, QColor, QPainter, QPen, QFont, QBrush, QKeySequence, QShortcut,
    QIcon, QPixmap,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QApplication, QLabel, QSystemTrayIcon, QMenu,
)

from ..config.display.display_data import DisplayModeConfig

log = logging.getLogger("mediabridge.display.window")

BADGE_MARGIN = 18
BADGE_PAD_H  = 14
BADGE_PAD_V  = 8
BADGE_RADIUS = 10
BADGE_FONT_SIZE = 12


# Input overlay — a transparent sibling that sits on top and eats all events
class _InputOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.BlankCursor)
        self.raise_()

    def mousePressEvent(self, e):   e.accept()
    def mouseReleaseEvent(self, e): e.accept()
    def mouseMoveEvent(self, e):    e.accept()
    def wheelEvent(self, e):        e.accept()
    def keyPressEvent(self, e):     e.accept()
    def keyReleaseEvent(self, e):   e.accept()
    def contextMenuEvent(self, e):  e.accept()


# Exit badge — semi-transparent corner pill drawn directly on the window
class _ExitBadge(QWidget):
    def __init__(
        self,
        hotkey: str,
        position: str,
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._position = position
        self._alpha = 220         # starts fully visible
        self._text = f"{hotkey}  to exit"

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(QFont("Segoe UI", BADGE_FONT_SIZE, QFont.Weight.DemiBold))

        # Size the badge to fit the text
        fm = self.fontMetrics()
        tw = fm.horizontalAdvance(self._text)
        th = fm.height()
        self._w = tw + BADGE_PAD_H * 2
        self._h = th + BADGE_PAD_V * 2
        self.setFixedSize(self._w, self._h)

        # Fade-out timer — starts 5 s after construction
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.setInterval(5_000)
        self._fade_timer.timeout.connect(self._start_fade)
        self._fade_timer.start()

        self._fade_step = QTimer(self)
        self._fade_step.setInterval(40)
        self._fade_step.timeout.connect(self._do_fade)

        self._position_badge()

    def _position_badge(self) -> None:
        if not self.parent():
            return
        pw, ph = self.parent().width(), self.parent().height()
        pos = self._position
        m = BADGE_MARGIN
        if pos == "top-left":
            self.move(m, m)
        elif pos == "top-right":
            self.move(pw - self._w - m, m)
        elif pos == "bottom-left":
            self.move(m, ph - self._h - m)
        else:  # bottom-right
            self.move(pw - self._w - m, ph - self._h - m)

    def flash(self) -> None:

        self._alpha = 220
        self._fade_step.stop()
        self.update()
        self._fade_timer.start()

    def _start_fade(self) -> None:
        self._fade_step.start()

    def _do_fade(self) -> None:
        self._alpha = max(0, self._alpha - 8)
        self.update()
        if self._alpha == 0:
            self._fade_step.stop()

    def paintEvent(self, _) -> None:  # noqa: ANN001
        if self._alpha == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._alpha / 255.0)

        # Background pill
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(10, 10, 20, 200)))
        p.drawRoundedRect(0, 0, self._w, self._h, BADGE_RADIUS, BADGE_RADIUS)

        # Border
        p.setPen(QPen(QColor(79, 142, 247, 180), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(1, 1, self._w - 2, self._h - 2, BADGE_RADIUS - 1, BADGE_RADIUS - 1)

        # Text
        p.setPen(QColor(220, 230, 255, 240))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self._text)

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self._position_badge()


# System tray helper
def _make_tray_icon(stop_callback) -> QSystemTrayIcon | None:
    if not QSystemTrayIcon.isSystemTrayAvailable():
        log.warning("System tray not available on this platform")
        return None

    # Build a tiny coloured square as the tray icon (no asset required)
    px = QPixmap(32, 32)
    px.fill(QColor(79, 142, 247))
    p = QPainter(px)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255))
    p.drawEllipse(8, 8, 16, 16)
    p.end()

    tray = QSystemTrayIcon(QIcon(px))
    menu = QMenu()

    stop_action = QAction("⏹  Stop display")
    stop_action.triggered.connect(stop_callback)
    menu.addAction(stop_action)

    quit_action = QAction("Quit MediaBridge")
    quit_action.triggered.connect(QApplication.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("MediaBridge Display — running")
    tray.activated.connect(lambda reason: (
        stop_callback()
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    ))
    tray.show()
    return tray


# Main display window
class DisplayWindow(QWidget):
    def __init__(self, config: DisplayModeConfig) -> None:
        super().__init__(None, Qt.Window)
        self._config = config
        self._view: QWidget | None = None
        self._overlay: _InputOverlay | None = None
        self._badge: _ExitBadge | None = None
        self._tray: QSystemTrayIcon | None = None

        self.setWindowTitle("MediaBridge Display")
        self.setStyleSheet("background: #000000;")

        # Root layout holds only the content view; overlay + badge are siblings
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._view = self._build_view()
        if self._view:
            self._root_layout.addWidget(self._view)

        self._position_on_screen()

        # ── Exit hotkey — always active ───────────────────────────────────────
        shortcut = QShortcut(QKeySequence(config.exit_hotkey), self)
        shortcut.setContext(Qt.ApplicationShortcut)   # works even when not focused
        shortcut.activated.connect(self.stop)
        log.info("Exit hotkey registered: %s", config.exit_hotkey)

        # ── Input blocking ────────────────────────────────────────────────────
        if not config.controllable:
            self._install_input_block()

        # ── Exit badge (deferred until after first show/resize) ───────────────
        if config.show_exit_badge:
            QTimer.singleShot(200, self._create_badge)

        # ── System tray ───────────────────────────────────────────────────────
        if config.system_tray_exit:
            self._tray = _make_tray_icon(self.stop)

    # ── Public API ────────────────────────────────────────────────────────────
    def start(self) -> None:
        self._position_on_screen()

        if self._config.fullscreen:
            self.showFullScreen()
        else:
            self.showNormal()

        if self._view and hasattr(self._view, "start"):
            self._view.start()

        # Raise overlay above the view after show (WebEngine creates its native
        # child window during showFullScreen, so we must raise after)
        if self._overlay:
            QTimer.singleShot(300, self._overlay.raise_)
            QTimer.singleShot(300, self._overlay.setFocus)

        log.info(
            "DisplayWindow started (content=%s, fullscreen=%s, controllable=%s)",
            self._config.content_type,
            self._config.fullscreen,
            self._config.controllable,
        )

    def stop(self) -> None:
        if self._view and hasattr(self._view, "stop"):
            self._view.stop()
        if self._tray:
            self._tray.hide()
            self._tray = None
        self.hide()
        self.closed.emit()
        log.info("DisplayWindow stopped")

    from PySide6.QtCore import Signal
    closed = Signal()

    # ── Input blocking ────────────────────────────────────────────────────────
    def _install_input_block(self) -> None:
        self._overlay = _InputOverlay(self)
        self._overlay.setGeometry(self.rect())
        self._overlay.show()
        self._overlay.raise_()

        # Also set mouse transparency on the view itself for non-native widgets
        if self._view:
            self._view.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._view.setFocusPolicy(Qt.NoFocus)

    # ── Badge ─────────────────────────────────────────────────────────────────
    def _create_badge(self) -> None:
        self._badge = _ExitBadge(
            self._config.exit_hotkey,
            self._config.exit_badge_position,
            self,
        )
        self._badge.show()
        self._badge.raise_()

    # ── View factory ─────────────────────────────────────────────────────────
    def _build_view(self) -> QWidget | None:
        cfg = self._config
        ct = cfg.content_type

        if ct == "url":
            from .views.url_view import URLView
            return URLView(cfg.url, cfg.url_refresh_minutes)

        elif ct == "image":
            from .views.image_view import ImageCarouselView
            return ImageCarouselView(
                cfg.image_paths,
                cfg.image_interval_seconds,
                cfg.image_screensaver_mode,
                cfg.image_fit,
            )

        elif ct == "pdf":
            from .views.pdf_view import PDFView
            return PDFView(cfg.pdf_path, cfg.pdf_page_interval_seconds, cfg.pdf_loop)

        elif ct == "video":
            from .views.video_view import VideoView
            return VideoView(cfg.video_path, cfg.video_loop, cfg.video_muted)

        elif ct == "stream":
            from .views.stream_view import StreamView
            return StreamView(
                cfg.stream_url,
                cfg.stream_autoplay,
                cfg.stream_loop,
                cfg.stream_muted,
            )

        else:
            log.error("Unknown content_type: %s", ct)
            lbl = QLabel(f"Unknown content type: {ct}", self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #F75F5F; font-size: 18px;")
            return lbl

    # ── Screen positioning ────────────────────────────────────────────────────
    def _position_on_screen(self) -> None:
        screens = QApplication.screens()
        idx = self._config.target_screen_index
        if idx >= len(screens):
            log.warning(
                "Screen index %d out of range (%d screens), using primary",
                idx, len(screens),
            )
            idx = 0
        geo = screens[idx].geometry()
        self.setGeometry(geo)
        log.debug("Positioned on screen %d: %s", idx, geo)

    # ── Resize: keep overlay + badge filling the window ───────────────────────
    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        if self._overlay:
            self._overlay.setGeometry(self.rect())
            self._overlay.raise_()
        if self._badge:
            self._badge._position_badge()
            self._badge.raise_()

    # ── Mouse move: flash badge on any activity ───────────────────────────────
    def mouseMoveEvent(self, event) -> None:  # noqa: ANN001
        if self._badge:
            self._badge.flash()
        super().mouseMoveEvent(event)

    # ── Keyboard: Escape as secondary exit (when controllable) ───────────────
    def keyPressEvent(self, event) -> None:  # noqa: ANN001
        if event.key() == Qt.Key_Escape:
            self.stop()
        super().keyPressEvent(event)