"""
ControlMode — orchestrator for the single-screen control module.

Supports two sub-modes:
1. "media"      — Single-screen media viewer with controls
2. "restaurant" — Restaurant ordering kiosk

Reads config from AppState, launches the appropriate window fullscreen,
and provides lifecycle management (launch/close) with exit gesture support.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtWidgets import QWidget

from core.app_state import AppState
from ui.themes.theme import ThemeManager
from ui.windows.control.media.media_window import MediaWindow
from ui.windows.control.media.media_loader import MediaLoader
from ui.windows.control.restaurant.restaurant_window import RestaurantWindow

logger = logging.getLogger(__name__)


class ControlMode:
    def __init__(
        self,
        sub_mode: str = "media",
        tm: ThemeManager | None = None,
        # Media sub-mode params
        media_records: list[dict] | None = None,
        local_dir: str | None = None,
        remote_url: str | None = None,
        remote_headers: dict | None = None,
        screensaver_cfg: dict | None = None,
        # Restaurant sub-mode params
        menu_source: str | None = None,
        restaurant_cfg: dict | None = None,
        # General
        on_exit: callable | None = None,
        on_order: callable | None = None,
    ) -> None:
        self._sub_mode       = sub_mode
        self._tm             = tm or AppState.instance().theme_manager
        self._state          = AppState.instance()
        self._on_exit        = on_exit
        self._on_order       = on_order

        # Media params
        self._media_records  = media_records
        self._local_dir      = local_dir
        self._remote_url     = remote_url
        self._remote_headers = remote_headers or {}
        self._screensaver_cfg = screensaver_cfg or {}

        # Restaurant params
        self._menu_source    = menu_source
        self._restaurant_cfg = restaurant_cfg or {}

        self._window: QWidget | None = None

    # ── Public API ────────────────────────────────────────────────

    def launch(self, screen_index: int | None = None) -> None:
        logger.info("ControlMode.launch sub_mode=%s", self._sub_mode)

        if self._sub_mode == "restaurant":
            self._window = RestaurantWindow(
                tm=self._tm,
                menu_source=self._menu_source,
                restaurant_cfg=self._restaurant_cfg,
                on_exit=self._handle_exit,
            )
            if self._on_order:
                self._window.order_submitted.connect(self._on_order)
        else:
            # Media mode — create window first, then load records async
            self._window = MediaWindow(
                tm=self._tm,
                records=[],
                on_exit=self._handle_exit,
                screensaver_cfg=self._screensaver_cfg,
            )
            # Load records via MediaLoader (supports media.json, API, or scan)
            self._media_loader = MediaLoader(
                local_dir=self._local_dir,
                remote_url=self._remote_url,
                remote_headers=self._remote_headers,
            )
            self._media_loader.loaded.connect(self._window.set_records)
            self._media_loader.error.connect(
                lambda e: logger.warning("MediaLoader error: %s", e)
            )

        # Assign to screen
        screens = QGuiApplication.screens()
        display_cfg = self._state.section("display")
        idx = screen_index if screen_index is not None else display_cfg.get("monitor_index", 0)
        idx = min(idx, len(screens) - 1)

        screen = screens[idx]
        geo = screen.geometry()
        self._window.setGeometry(geo)

        if display_cfg.get("fullscreen", True):
            self._window.showFullScreen()
        else:
            self._window.show()

        # Start async media loading after window is visible
        if hasattr(self, "_media_loader"):
            self._media_loader.load()

        logger.info("ControlMode: window shown on screen %d %s", idx, geo)

    def close(self) -> None:
        """Close the control window."""
        logger.info("ControlMode.close")
        if self._window:
            self._window.close()
            self._window = None

    @property
    def is_active(self) -> bool:
        return self._window is not None and self._window.isVisible()

    # ── Internals ─────────────────────────────────────────────────

    def _handle_exit(self) -> None:
        logger.info("ControlMode: exit gesture — closing")
        self.close()
        if self._on_exit:
            self._on_exit()
