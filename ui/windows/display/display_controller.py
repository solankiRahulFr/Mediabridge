
from __future__ import annotations
import logging

from ui.windows.config.display.display_data import DisplayModeConfig
from ui.windows.display.display_window import DisplayWindow

log = logging.getLogger("mediabridge.display.controller")


class DisplayController:
    def __init__(self, config: DisplayModeConfig | None = None) -> None:
        self._config = config or DisplayModeConfig()
        self._window: DisplayWindow | None = None

    # ── Public API ────────────────────────────────────────────────────────────
    @property
    def config(self) -> DisplayModeConfig:
        return self._config

    def update_config(self, config: DisplayModeConfig) -> None:
        self._config = config

    def launch(self) -> None:
        self.close()
        self._window = DisplayWindow(self._config)
        self._window.start()
        log.info("Display launched")

    def relaunch(self) -> None:
        log.info("Relaunching display with updated config")
        self.launch()

    def close(self) -> None:
        if self._window is not None:
            self._window.stop()
            self._window.deleteLater()
            self._window = None

    @property
    def is_active(self) -> bool:
        return self._window is not None and self._window.isVisible()
