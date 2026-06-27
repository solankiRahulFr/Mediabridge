from __future__ import annotations

import logging
import time
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer, QEvent, Signal
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QKeySequence, QShortcut, QColor, QPen,
    QBrush, QIcon, QAction,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QLabel, QStackedWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QApplication, QSystemTrayIcon, QMenu,
)

from core.app_state import AppState
from ui.themes.theme import ThemeManager
from ui.windows.control.media.media_toolbar import MediaToolbar
from ui.windows.control.media.media_browser import MediaBrowser
from ui.windows.control.media.touch_image_viewer import TouchImageViewer
from ui.windows.control.media.touch_pdf_viewer import TouchPDFViewer

logger = logging.getLogger(__name__)

_PAGE_GALLERY = 0
_PAGE_VIDEO   = 1
_PAGE_PDF     = 2
_PAGE_IMAGE   = 3

_EXIT_TAP_COUNT    = 6
_EXIT_TAP_WINDOW_S = 3.0

_DEFAULT_SCREENSAVER_TIMEOUT_S = 120  # 2 minutes

_EXIT_HOTKEY       = "Ctrl+Shift+Q"
_BADGE_MARGIN      = 18
_BADGE_PAD_H       = 14
_BADGE_PAD_V       = 8
_BADGE_RADIUS      = 10
_BADGE_FONT_SIZE   = 12


# Exit badge — semi-transparent corner pill (mirrors display mode)
class _ExitBadge(QWidget):
    def __init__(self, hotkey: str, parent: QWidget) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._alpha = 220
        self._text = f"{hotkey}  to exit"

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(QFont("Segoe UI", _BADGE_FONT_SIZE, QFont.Weight.DemiBold))

        fm = self.fontMetrics()
        self._w = fm.horizontalAdvance(self._text) + _BADGE_PAD_H * 2
        self._h = fm.height() + _BADGE_PAD_V * 2
        self.setFixedSize(self._w, self._h)

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
        pw = self.parent().width()
        self.move(pw - self._w - _BADGE_MARGIN, _BADGE_MARGIN)

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

    def paintEvent(self, _) -> None:
        if self._alpha == 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._alpha / 255.0)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(10, 10, 20, 200)))
        p.drawRoundedRect(0, 0, self._w, self._h, _BADGE_RADIUS, _BADGE_RADIUS)
        p.setPen(QPen(QColor(79, 142, 247, 180), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(1, 1, self._w - 2, self._h - 2, _BADGE_RADIUS - 1, _BADGE_RADIUS - 1)
        p.setPen(QColor(220, 230, 255, 240))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignCenter, self._text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_badge()


# System tray helper
def _make_tray_icon(stop_cb, back_cb) -> QSystemTrayIcon | None:
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    px = QPixmap(32, 32)
    px.fill(QColor(79, 142, 247))
    p = QPainter(px)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255))
    p.drawEllipse(8, 8, 16, 16)
    p.end()

    tray = QSystemTrayIcon(QIcon(px))
    menu = QMenu()

    back_action = QAction("↩  Back to launcher")
    back_action.triggered.connect(back_cb)
    menu.addAction(back_action)

    stop_action = QAction("⏹  Close media viewer")
    stop_action.triggered.connect(stop_cb)
    menu.addAction(stop_action)

    quit_action = QAction("Quit MediaBridge")
    quit_action.triggered.connect(QApplication.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.setToolTip("MediaBridge Media — running")
    tray.activated.connect(lambda reason: (
        back_cb()
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick
        else None
    ))
    tray.show()
    return tray


# Screensaver overlay
class _ScreensaverOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: #000;")
        self.hide()

        self._player: QMediaPlayer | None = None
        self._audio: QAudioOutput | None = None
        self._video_widget: QVideoWidget | None = None
        self._image_label: QLabel | None = None
        self._clock_label: QLabel | None = None
        self._clock_timer: QTimer | None = None

        self._mode = "dim"  # "dim" | "image" | "video"

        self._build_dim()

    def _build_dim(self) -> None:
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        self._clock_label = QLabel("", self)
        self._clock_label.setAlignment(Qt.AlignCenter)
        self._clock_label.setStyleSheet(
            "color: rgba(255,255,255,0.4); font-size: 48px; background: transparent;"
        )
        lay.addWidget(self._clock_label)

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._update_clock)

    def configure(self, ss_type: str = "none", ss_source: str = "") -> None:
        self._mode = ss_type if ss_type in ("image", "video") else "dim"
        self._ss_source = ss_source

    def activate(self) -> None:
        self.setGeometry(self.parent().rect())
        self.raise_()

        if self._mode == "image" and self._ss_source:
            self._show_image()
        elif self._mode == "video" and self._ss_source:
            self._show_video()
        else:
            self._show_dim()

        self.show()

    def deactivate(self) -> None:
        if self._player:
            self._player.stop()
        if self._clock_timer:
            self._clock_timer.stop()
        self.hide()

    def _show_dim(self) -> None:
        if self._clock_label:
            self._update_clock()
            self._clock_timer.start()
            self._clock_label.show()
        if self._video_widget:
            self._video_widget.hide()
        if self._image_label:
            self._image_label.hide()

    def _show_image(self) -> None:
        if self._clock_timer:
            self._clock_timer.stop()
        if self._clock_label:
            self._clock_label.hide()

        if not self._image_label:
            self._image_label = QLabel(self)
            self._image_label.setAlignment(Qt.AlignCenter)
            self._image_label.setStyleSheet("background: #000;")
            self.layout().addWidget(self._image_label)

        px = QPixmap(self._ss_source)
        if not px.isNull():
            w, h = self.width() or 1920, self.height() or 1080
            self._image_label.setPixmap(
                px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self._image_label.show()

    def _show_video(self) -> None:
        if self._clock_timer:
            self._clock_timer.stop()
        if self._clock_label:
            self._clock_label.hide()

        if not self._video_widget:
            self._video_widget = QVideoWidget(self)
            self._audio = QAudioOutput(self)
            self._audio.setMuted(True)
            self._player = QMediaPlayer(self)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(self._video_widget)
            self._player.mediaStatusChanged.connect(self._on_video_status)
            self.layout().addWidget(self._video_widget)

        self._video_widget.show()
        src = self._ss_source
        if src.startswith("http"):
            self._player.setSource(QUrl(src))
        else:
            self._player.setSource(QUrl.fromLocalFile(src))
        self._player.play()

    def _on_video_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self._player:
            self._player.setPosition(0)
            self._player.play()

    def _update_clock(self) -> None:
        import datetime
        now = datetime.datetime.now()
        self._clock_label.setText(now.strftime("%H:%M:%S"))

    # Any touch/click dismisses the screensaver
    def mousePressEvent(self, event) -> None:
        self.deactivate()
        event.accept()

    def touchEvent(self, event) -> None:
        self.deactivate()
        event.accept()


# Main media window
class MediaWindow(QWidget):
    closed = Signal()

    def __init__(
        self,
        tm: ThemeManager | None = None,
        records: list[dict] | None = None,
        on_exit: callable | None = None,
        screensaver_cfg: dict | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tm = tm or AppState.instance().theme_manager
        self._records = records or []
        self._current_idx = 0
        self._on_exit = on_exit
        self._exit_taps: list[float] = []
        self._badge: _ExitBadge | None = None
        self._tray: QSystemTrayIcon | None = None

        self.setWindowTitle("MediaBridge — Media Viewer")
        self.setStyleSheet(f"background: {self._tm.color('bg')};")

        self._build()
        self._connect_toolbar()

        # ── Screensaver ───────────────────────────────────────────
        ss_cfg = screensaver_cfg or {}
        self._screensaver = _ScreensaverOverlay(self)
        self._screensaver.configure(
            ss_type=ss_cfg.get("type", "dim"),
            ss_source=ss_cfg.get("source", ""),
        )
        timeout_s = ss_cfg.get("timeout_seconds", _DEFAULT_SCREENSAVER_TIMEOUT_S)
        self._inactivity_timer = QTimer(self)
        self._inactivity_timer.setSingleShot(True)
        self._inactivity_timer.setInterval(timeout_s * 1000)
        self._inactivity_timer.timeout.connect(self._on_inactivity)
        self._inactivity_timer.start()

        # Install global event filter for activity detection
        self.installEventFilter(self)

        # ── Exit hotkey: Ctrl+Shift+Q → exit to launcher ──────────
        exit_shortcut = QShortcut(QKeySequence(_EXIT_HOTKEY), self)
        exit_shortcut.setContext(Qt.ApplicationShortcut)
        exit_shortcut.activated.connect(self._exit_to_launcher)
        logger.info("Exit hotkey registered: %s", _EXIT_HOTKEY)

        # ── Exit badge (top-right pill) ───────────────────────────
        QTimer.singleShot(200, self._create_badge)

        # ── System tray ───────────────────────────────────────────
        self._tray = _make_tray_icon(
            stop_cb=self._exit_to_launcher,
            back_cb=self._exit_to_launcher,
        )

        # Load records into gallery
        if self._records:
            self._browser.set_records(self._records)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Exit gesture area (top-left invisible tap zone)
        self._exit_zone = QLabel(self)
        self._exit_zone.setFixedSize(60, 60)
        self._exit_zone.setStyleSheet("background: transparent;")
        self._exit_zone.mousePressEvent = self._on_exit_tap
        self._exit_zone.raise_()

        # Media stack
        self._stack = QStackedWidget()

        # Page 0: gallery browser
        self._browser = MediaBrowser(self._tm)
        self._browser.media_selected.connect(self._on_gallery_select)
        self._stack.addWidget(self._browser)

        # Page 1: video
        self._video_widget = QVideoWidget()
        self._video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        self._audio = QAudioOutput()
        self._audio.setVolume(0.8)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video_widget)
        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)
        self._player.playbackStateChanged.connect(self._on_playback_state)
        self._stack.addWidget(self._video_widget)

        # Page 2: PDF with touch
        self._pdf_viewer = TouchPDFViewer()
        self._pdf_viewer.view.pageNavigator().currentPageChanged.connect(self._on_pdf_page)
        self._stack.addWidget(self._pdf_viewer)

        # Page 3: image with touch
        self._image_viewer = TouchImageViewer()
        self._stack.addWidget(self._image_viewer)

        root.addWidget(self._stack, 1)

        # Toolbar overlay
        self._toolbar = MediaToolbar(self._tm)
        root.addWidget(self._toolbar)

    def _connect_toolbar(self) -> None:
        tb = self._toolbar
        tb.play_requested.connect(self._player.play)
        tb.pause_requested.connect(self._player.pause)
        tb.seek_requested.connect(self._player.setPosition)
        tb.volume_changed.connect(lambda v: self._audio.setVolume(v / 100.0))
        tb.mute_requested.connect(self._toggle_mute)

        tb.pdf_next_page.connect(self._pdf_next)
        tb.pdf_prev_page.connect(self._pdf_prev)

        tb.zoom_in.connect(self._on_zoom_in)
        tb.zoom_out.connect(self._on_zoom_out)
        tb.zoom_reset.connect(self._on_zoom_reset)

        tb.next_requested.connect(self._next_item)
        tb.prev_requested.connect(self._prev_item)
        tb.close_requested.connect(self._close_media)

    # ── Public API ────────────────────────────────────────────────

    def set_records(self, records: list[dict]) -> None:
        self._records = records
        self._current_idx = 0
        self._browser.set_records(records)
        self._stack.setCurrentIndex(_PAGE_GALLERY)
        self._toolbar.hide_bar()

    # ── Gallery selection ─────────────────────────────────────────

    def _on_gallery_select(self, record_index: int) -> None:
        self._current_idx = record_index
        self._show_record(record_index)

    # ── Zoom routing ──────────────────────────────────────────────

    def _on_zoom_in(self) -> None:
        page = self._stack.currentIndex()
        if page == _PAGE_IMAGE:
            self._image_viewer.zoom_in()
        elif page == _PAGE_PDF:
            self._pdf_viewer.zoom_in()

    def _on_zoom_out(self) -> None:
        page = self._stack.currentIndex()
        if page == _PAGE_IMAGE:
            self._image_viewer.zoom_out()
        elif page == _PAGE_PDF:
            self._pdf_viewer.zoom_out()

    def _on_zoom_reset(self) -> None:
        page = self._stack.currentIndex()
        if page == _PAGE_IMAGE:
            self._image_viewer.zoom_reset()
        elif page == _PAGE_PDF:
            self._pdf_viewer.zoom_reset()

    # ── Mute toggle ───────────────────────────────────────────────

    def _toggle_mute(self) -> None:
        muted = not self._audio.isMuted()
        self._audio.setMuted(muted)
        self._toolbar.set_muted(muted)

    # ── Navigation ────────────────────────────────────────────────

    def _next_item(self) -> None:
        if not self._records:
            return
        self._current_idx = (self._current_idx + 1) % len(self._records)
        self._show_record(self._current_idx)

    def _prev_item(self) -> None:
        if not self._records:
            return
        self._current_idx = (self._current_idx - 1) % len(self._records)
        self._show_record(self._current_idx)

    def _show_record(self, idx: int) -> None:
        if idx >= len(self._records):
            return
        record = self._records[idx]
        ct = record.get("content_type", "unknown")

        # Stop current media
        self._player.stop()
        self._player.setSource(QUrl())

        if ct == "video":
            src = record.get("video", "")
            if src:
                self._stack.setCurrentIndex(_PAGE_VIDEO)
                if src.startswith("http"):
                    self._player.setSource(QUrl(src))
                else:
                    self._player.setSource(QUrl.fromLocalFile(src))
                self._player.play()
                self._toolbar.show_for("video")
        elif ct == "pdf":
            src = record.get("pdf", "")
            if src:
                self._stack.setCurrentIndex(_PAGE_PDF)
                self._pdf_viewer.load(src)
                self._toolbar.set_pdf_count(self._pdf_viewer.page_count())
                self._toolbar.show_for("pdf")
        elif ct == "image":
            src = record.get("image") or record.get("primary_image", "")
            if src:
                self._stack.setCurrentIndex(_PAGE_IMAGE)
                self._image_viewer.load(src)
                self._toolbar.show_for("image")
        else:
            self._stack.setCurrentIndex(_PAGE_GALLERY)
            self._toolbar.hide_bar()

    def _close_media(self) -> None:
        self._player.stop()
        self._player.setSource(QUrl())
        self._image_viewer.clear()
        self._pdf_viewer.close_doc()
        self._stack.setCurrentIndex(_PAGE_GALLERY)
        self._toolbar.hide_bar()

    def _exit_to_launcher(self) -> None:
        logger.info("Exit workaround triggered — closing media viewer")
        self._player.stop()
        self._player.setSource(QUrl())
        if self._tray:
            self._tray.hide()
            self._tray = None
        self.hide()
        self.closed.emit()
        if self._on_exit:
            self._on_exit()

    # ── Video feedback ────────────────────────────────────────────

    def _on_position(self, ms: int) -> None:
        self._toolbar.set_position(ms)

    def _on_duration(self, ms: int) -> None:
        self._toolbar.set_duration(ms)

    def _on_playback_state(self, state: QMediaPlayer.PlaybackState) -> None:
        mapping = {
            QMediaPlayer.PlaybackState.PlayingState: "playing",
            QMediaPlayer.PlaybackState.PausedState: "paused",
            QMediaPlayer.PlaybackState.StoppedState: "stopped",
        }
        self._toolbar.set_playback_state(mapping.get(state, "stopped"))

    # ── PDF navigation ────────────────────────────────────────────

    def _pdf_next(self) -> None:
        self._pdf_viewer.next_page()

    def _pdf_prev(self) -> None:
        self._pdf_viewer.prev_page()

    def _on_pdf_page(self, page: int) -> None:
        self._toolbar.set_pdf_page(page)

    # ── Screensaver / inactivity ──────────────────────────────────

    def _on_inactivity(self) -> None:
        logger.info("Inactivity timeout — activating screensaver")
        self._screensaver.activate()

    def _reset_activity(self) -> None:
        """Reset the inactivity timer on any user interaction."""
        if self._screensaver.isVisible():
            self._screensaver.deactivate()
        self._inactivity_timer.start()

    def eventFilter(self, obj, event: QEvent) -> bool:
        t = event.type()
        if t in (
            QEvent.MouseButtonPress, QEvent.MouseMove,
            QEvent.TouchBegin, QEvent.TouchUpdate,
            QEvent.KeyPress, QEvent.Wheel,
        ):
            self._reset_activity()
        return super().eventFilter(obj, event)

    # ── Exit gesture ──────────────────────────────────────────────

    def _on_exit_tap(self, _) -> None:
        now = time.monotonic()
        self._exit_taps = [t for t in self._exit_taps if now - t < _EXIT_TAP_WINDOW_S]
        self._exit_taps.append(now)
        if len(self._exit_taps) >= _EXIT_TAP_COUNT:
            self._exit_taps.clear()
            self._exit_to_launcher()

    # ── Badge ─────────────────────────────────────────────────────

    def _create_badge(self) -> None:
        self._badge = _ExitBadge(_EXIT_HOTKEY, self)
        self._badge.show()
        self._badge.raise_()

    # ── Keyboard: Escape → back to gallery or exit ────────────────

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            if self._stack.currentIndex() != _PAGE_GALLERY:
                self._close_media()
            else:
                self._exit_to_launcher()
            return
        super().keyPressEvent(event)

    # ── Mouse: flash badge on movement ────────────────────────────

    def mouseMoveEvent(self, event) -> None:
        if self._badge:
            self._badge.flash()
        super().mouseMoveEvent(event)

    # ── Resize ────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._screensaver.isVisible():
            self._screensaver.setGeometry(self.rect())
        if self._badge:
            self._badge._position_badge()
            self._badge.raise_()
        self._exit_zone.raise_()

    # ── Theme ─────────────────────────────────────────────────────

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self.setStyleSheet(f"background: {tm.color('bg')};")
        self._toolbar.update_theme(tm)

