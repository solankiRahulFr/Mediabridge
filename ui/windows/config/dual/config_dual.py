from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QCursor, QFont

from core.app_state import get_state
from core.theme import ThemeManager
from ui.widgets.navbar import NavTabs
from ui.widgets.header import Header
from core.i18n_mixin import I18nMixin
from .panels.display_panel import DisplayPanel
from .panels.behavior_panel import BehaviorPanel
from .panels.mapping_panel import MappingPanel
from .panels.header_panel import HeaderPanel
from core.configio import ConfigIO

log = logging.getLogger(__name__)



class ConfigWindowDual(I18nMixin, QWidget):

    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None, is_dark: bool = True):
        super().__init__(parent)
        self._state = get_state()
        self._is_dark = self._state.theme.is_dark if self._state.theme else is_dark

        if self._state.theme:
            self._tm = self._state.theme
        else:
            self._tm = ThemeManager(self._is_dark)

        self._state.lang.on_change(lambda _code: self.retranslate_ui())

        self._build_ui()
        self._connect_signals()
        self._tm.apply(self)

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header (pinned to top, no stretch above it) ───────────────────────
        root.addWidget(self._build_header())

        # ── body (centered vertically in remaining space) ─────────────────────
        body = QVBoxLayout()
        body.setSpacing(12)
        body.setContentsMargins(24, 24, 24, 24)

        self.label = QLabel("Building the module")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #5C5EAA;
            }
        """)

        body.addWidget(self.label)

        # Wrap body in a widget so we can sandwich it between stretches
        body_widget = QWidget()
        body_widget.setLayout(body)

        root.addStretch()
        root.addWidget(body_widget)
        root.addStretch()

        # ── animation ─────────────────────────────────────────────────────────
        self.dots = ""
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(500)

        self.setLayout(root)

    def animate(self):
        self.dots += "."
        if len(self.dots) > 5:
            self.dots = ""
        self.label.setText(f"Building the module {self.dots}")

    def _build_header(self) -> QWidget:
        self._header = Header(show_back=True)
        self._header.back_requested.connect(self.back_requested.emit)
        return self._header


 
    def _connect_signals(self):
        self._header.theme_toggle.toggled.connect(self._on_theme_toggle)

    def retranslate_ui(self) -> None:
        self._do_retranslate()
        if hasattr(self, "_panels"):
            for panel in self._panels.values():
                if hasattr(panel, 'retranslate_ui'):
                    panel.retranslate_ui()

    def showEvent(self, event):
        super().showEvent(event)
        if self._state.theme:
            is_dark = self._state.theme.is_dark
            if is_dark != self._is_dark:
                self._is_dark = is_dark
                self._tm.set_dark(is_dark)
                self._tm.apply(self)
                if hasattr(self, "_panels"):
                    for p in self._panels.values():
                        self._tm.apply(p)
        self._header.sync_theme()

    def _on_theme_toggle(self, is_dark: bool):
        self._is_dark = is_dark
        self._tm.set_dark(is_dark)
        self._state.set("is_dark", is_dark)
        self._tm.apply(self)
        # Propagate to child panels
        if hasattr(self, "_panels"):
            for p in self._panels.values():
                self._tm.apply(p)
        log.info("Config theme toggled: is_dark=%s", is_dark)

