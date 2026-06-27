
from __future__ import annotations
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

log = logging.getLogger("mediabridge.display.video")


def _is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


class VideoView(QWidget):
    def __init__(
        self,
        video_path: str,
        loop: bool = True,
        muted: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = video_path
        self._loop = loop
        self._muted = muted

        self.setStyleSheet("background: #000000;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._video_widget = QVideoWidget(self)
        layout.addWidget(self._video_widget)

        self._overlay = QLabel(self)
        self._overlay.setAlignment(Qt.AlignCenter)
        self._overlay.setStyleSheet(
            "color: #5C6080; font-size: 18px; background: transparent;"
        )
        self._overlay.hide()

        self._player = QMediaPlayer(self)
        self._audio = QAudioOutput(self)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video_widget)
        self._audio.setMuted(muted)

        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.errorOccurred.connect(self._on_error)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self) -> None:
        if not self._path:
            self._show_overlay("No video source configured.")
            return

        if _is_url(self._path):
            # Direct HTTP stream (mp4, m3u8, etc.)
            log.info("Video: loading HTTP stream: %s", self._path)
            self._player.setSource(QUrl(self._path))
        else:
            if not Path(self._path).is_file():
                self._show_overlay(f"Video not found:\n{self._path}")
                return
            log.info("Video: loading local file: %s", self._path)
            self._player.setSource(QUrl.fromLocalFile(self._path))

        self._overlay.hide()
        self._player.play()

    def stop(self) -> None:
        self._player.stop()

    # ── Controls ──────────────────────────────────────────────────────────────
    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._audio.setMuted(muted)

    def set_loop(self, loop: bool) -> None:
        self._loop = loop

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._loop:
                log.debug("Video loop: restarting")
                self._player.setPosition(0)
                self._player.play()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._show_overlay(
                f"Cannot play:\n{self._path}\n\n"
                "For YouTube/Vimeo, use the Stream tab instead.\n"
                "For local files, check codec support."
            )

    def _on_error(self, error, error_string: str) -> None:
        log.error("QMediaPlayer error %s: %s", error, error_string)
        self._show_overlay(f"Playback error:\n{error_string}")

    def _show_overlay(self, text: str) -> None:
        self._overlay.setText(text)
        self._overlay.setGeometry(self.rect())
        self._overlay.show()
        self._overlay.raise_()

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())