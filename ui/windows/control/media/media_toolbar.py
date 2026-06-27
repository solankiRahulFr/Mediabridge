from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager

logger = logging.getLogger(__name__)


def _ms_to_str(ms: int) -> str:
    s = ms // 1000
    m = s // 60
    h = m // 60
    s %= 60
    m %= 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class MediaToolbar(QWidget):
    close_requested = Signal()
    next_requested = Signal()
    prev_requested = Signal()

    # Video signals
    play_requested = Signal()
    pause_requested = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)

    # PDF signals
    pdf_next_page = Signal()
    pdf_prev_page = Signal()
    pdf_page_requested = Signal(int)

    # Zoom signals
    zoom_in = Signal()
    zoom_out = Signal()
    zoom_reset = Signal()

    # Mute signal
    mute_requested = Signal()

    _BAR_H = 80

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._mode = "none"
        self._duration = 0
        self._page_count = 0

        self.setFixedHeight(0)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 8, 16, 8)
        root.setSpacing(6)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        # Navigation (prev/next media item)
        self._prev_media_btn = self._mk_btn("⏮", None)
        self._prev_media_btn.clicked.connect(self.prev_requested)
        self._next_media_btn = self._mk_btn("⏭", None)
        self._next_media_btn.clicked.connect(self.next_requested)

        # Video controls
        self._play_btn = self._mk_btn("▶", None)
        self._play_btn.clicked.connect(self.play_requested)
        self._pause_btn = self._mk_btn("⏸", None)
        self._pause_btn.clicked.connect(self.pause_requested)

        # PDF controls
        self._pdf_prev_btn = self._mk_btn("◀", None)
        self._pdf_prev_btn.clicked.connect(self.pdf_prev_page)
        self._pdf_next_btn = self._mk_btn("▶", None)
        self._pdf_next_btn.clicked.connect(self.pdf_next_page)
        self._page_lbl = QLabel("— / —")
        self._page_lbl.setObjectName("PageLabel")
        self._page_lbl.setFixedWidth(70)
        self._page_lbl.setAlignment(Qt.AlignCenter)

        # Zoom (shared by image + pdf)
        self._zoom_in_btn = self._mk_btn("＋", None)
        self._zoom_in_btn.clicked.connect(self.zoom_in)
        self._zoom_out_btn = self._mk_btn("－", None)
        self._zoom_out_btn.clicked.connect(self.zoom_out)
        self._zoom_reset_btn = self._mk_btn("⊡", None)
        self._zoom_reset_btn.clicked.connect(self.zoom_reset)

        # Volume + Mute
        self._mute_btn = self._mk_btn("🔊", None)
        self._mute_btn.clicked.connect(self.mute_requested)
        self._vol_slider = QSlider(Qt.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(80)
        self._vol_slider.setFixedWidth(80)
        self._vol_slider.valueChanged.connect(self.volume_changed)

        # Close
        self._close_btn = self._mk_btn("✕", None)
        self._close_btn.setObjectName("CloseMediaBtn")
        self._close_btn.clicked.connect(self.close_requested)

        # Time label
        self._time_lbl = QLabel("0:00 / 0:00")
        self._time_lbl.setObjectName("TimeLabel")

        for w in [
            self._prev_media_btn,
            self._play_btn, self._pause_btn,
            self._pdf_prev_btn, self._pdf_next_btn, self._page_lbl,
            self._zoom_in_btn, self._zoom_out_btn, self._zoom_reset_btn,
            self._mute_btn, self._vol_slider, self._time_lbl,
            self._next_media_btn,
        ]:
            ctrl_row.addWidget(w)

        ctrl_row.addStretch()
        ctrl_row.addWidget(self._close_btn)
        root.addLayout(ctrl_row)

        # Seek slider (video)
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setRange(0, 1000)
        self._seek_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._seek_slider.sliderMoved.connect(self._on_seek_moved)
        root.addWidget(self._seek_slider)

        self._apply_theme()

    def _mk_btn(self, icon: str, signal) -> QPushButton:
        btn = QPushButton(icon)
        btn.setObjectName("CtrlBtn")
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.PointingHandCursor)
        if signal is not None:
            btn.clicked.connect(signal)
        return btn

    # ── Public API ────────────────────────────────────────────────

    def show_for(self, content_type: str) -> None:
        self._mode = content_type
        self._update_visibility()
        self._slide(self._BAR_H)

    def hide_bar(self) -> None:
        self._slide(0)

    def set_position(self, ms: int) -> None:
        if self._duration:
            self._seek_slider.blockSignals(True)
            self._seek_slider.setValue(int(ms * 1000 / self._duration))
            self._seek_slider.blockSignals(False)
        self._time_lbl.setText(f"{_ms_to_str(ms)} / {_ms_to_str(self._duration)}")

    def set_duration(self, ms: int) -> None:
        self._duration = ms
        self._time_lbl.setText(f"0:00 / {_ms_to_str(ms)}")

    def set_playback_state(self, state: str) -> None:
        if state == "playing":
            self._play_btn.hide()
            self._pause_btn.show()
        else:
            self._play_btn.show()
            self._pause_btn.hide()

    def set_pdf_page(self, page: int) -> None:
        self._page_lbl.setText(f"{page + 1} / {self._page_count or '?'}")

    def set_pdf_count(self, count: int) -> None:
        self._page_count = count

    def set_muted(self, muted: bool) -> None:
        self._mute_btn.setText("🔇" if muted else "🔊")

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._apply_theme()

    # ── Internals ─────────────────────────────────────────────────

    def _update_visibility(self) -> None:
        is_video = self._mode == "video"
        is_pdf = self._mode == "pdf"
        is_zoom = self._mode in ("pdf", "image")

        self._play_btn.setVisible(is_video)
        self._pause_btn.setVisible(is_video)
        self._seek_slider.setVisible(is_video)
        self._time_lbl.setVisible(is_video)
        self._mute_btn.setVisible(is_video)
        self._vol_slider.setVisible(is_video)

        self._pdf_prev_btn.setVisible(is_pdf)
        self._pdf_next_btn.setVisible(is_pdf)
        self._page_lbl.setVisible(is_pdf)

        self._zoom_in_btn.setVisible(is_zoom)
        self._zoom_out_btn.setVisible(is_zoom)
        self._zoom_reset_btn.setVisible(is_zoom)

    def _slide(self, target_h: int) -> None:
        anim = QPropertyAnimation(self, b"maximumHeight", self)
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setStartValue(self.maximumHeight())
        anim.setEndValue(target_h)
        anim.start()
        self._anim = anim

    def _on_seek_moved(self, val: int) -> None:
        if self._duration:
            self.seek_requested.emit(int(self._duration * val / 1000))

    def _apply_theme(self) -> None:
        t = self._tm.colors
        self.setStyleSheet(
            f"QWidget {{"
            f"  background: {t['bg2']};"
            f"  border-top: 1px solid {t['border']};"
            f"}}"
            f"QPushButton#CtrlBtn {{"
            f"  background: {t['surface2']}; color: {t['text']};"
            f"  border: 1px solid {t['border']}; border-radius: 8px;"
            f"  font-size: 14px;"
            f"}}"
            f"QPushButton#CtrlBtn:hover {{"
            f"  background: {t['accent']}; color: #fff; border-color: {t['accent']};"
            f"}}"
            f"QPushButton#CloseMediaBtn {{"
            f"  background: transparent; color: {t['danger']};"
            f"  border: 1px solid {t['danger']}; border-radius: 8px;"
            f"}}"
            f"QPushButton#CloseMediaBtn:hover {{"
            f"  background: {t['danger']}; color: #fff;"
            f"}}"
            f"QLabel#PageLabel, QLabel#TimeLabel {{"
            f"  color: {t['text2']}; font-size: 11px; background: transparent;"
            f"}}"
            f"QSlider::groove:horizontal {{"
            f"  height: 4px; background: {t['border']}; border-radius: 2px;"
            f"}}"
            f"QSlider::handle:horizontal {{"
            f"  background: {t['accent']}; border: none;"
            f"  width: 14px; height: 14px; margin: -5px 0; border-radius: 7px;"
            f"}}"
            f"QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 2px; }}"
        )
