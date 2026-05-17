"""
Main Config Page  –  assembles all panels into a tabbed QStackedWidget and
wires up theme / language signals coming from the host application.

Uses the central ThemeManager (via ``get_state().theme``) and LanguageSwitcher
widget.  No direct JSON file reads.
"""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizePolicy, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCursor, QFont, QPixmap

from core.app_state import get_state
from core.theme import ThemeManager
from ui.themes.theme import THEMES
from ui.widgets.togglebutton import ThemeToggle
from ui.widgets.language_switcher import LanguageSwitcher
from .panels.display_panel import DisplayPanel
from .panels.behavior_panel import BehaviorPanel
from .panels.mapping_panel import MappingPanel
from .panels.header_panel import HeaderPanel
from core.configio import ConfigIO

log = logging.getLogger(__name__)
from ui.widgets.navbar import NavTabs



class ConfigWindow(QWidget):
    """
    Top-level configuration page.
    Emits ``config_saved(dict)`` when the user clicks Save.
    """
    config_saved = Signal(dict)
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None, is_dark: bool = True):
        super().__init__(parent)
        self._state = get_state()
        self._is_dark = is_dark

        # Use the central ThemeManager if available, else create a local one
        if self._state.theme:
            self._tm = self._state.theme
        else:
            self._tm = ThemeManager(self._is_dark)

        self._active_tab = "display"
        self.tabs= NavTabs(
            [
                ("display", "Display"),
                ("behavior", "Behavior"),
                ("header", "Header"),
                ("mapping", "Field Map"),
            ],
            tm=self._tm)
        self._panel_area = QStackedContent()
        self._build_ui()
        self._connect_signals()
        self._tm.apply(self)



    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addStretch()

        # ── header bar ────────────────────────────────────────────────────────
        root.addWidget(self._build_header())
        root.addStretch()
 
        self.tabs.set_active(self._active_tab)
        self.tabs.tab_changed.connect(self._switch_panel)
        # self._switch_panel(self._active_tab)
        root.addWidget(self.tabs)



        # ── body (panel) ────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        
        body.addWidget(self._panel_area, 1)

        root.addLayout(body, 1)

        # ── footer ────────────────────────────────────────────────────────────
        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        self.header = QWidget()
        self.header.setFixedHeight(64)
        hdr_lay = QHBoxLayout(self.header)
        self.header.setObjectName("Header")
        hdr_lay.setContentsMargins(32, 0, 32, 0)

        # logo / wordmark
        pixmap = QPixmap('ui/assets/images/mediabridge.png')
        scaled_pixmap = pixmap.scaled(
            48, 48,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        logo_image = QLabel()
        logo_image.setPixmap(scaled_pixmap)
        logo_font = QFont(); logo_font.setPointSize(13); logo_font.setWeight(QFont.Bold)
        logo_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        hdr_lay.addWidget(logo_image)
        hdr_lay.setSpacing(20)

        # Back button
        self.back_btn = QPushButton(self._state.lang.t("launch.back_btn"))
        self.back_btn.setFixedHeight(36)
        self.back_btn.setFixedWidth(80)
        bf = QFont(); bf.setPointSize(9); bf.setWeight(QFont.Medium)
        self.back_btn.setFont(bf)
        self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.back_btn.setStyleSheet((
            f"QPushButton {{ background: transparent; color: {self._tm.color('text2')}; "
            f"border: 1.5px solid {self._tm.color('border')}; border-radius: 8px; }}"
            f"QPushButton:hover {{ color: {self._tm.color('text')}; border-color: {self._tm.color('accent')}; }}"
        ))
        self.back_btn.clicked.connect(self.back_requested.emit)
        hdr_lay.addWidget(self.back_btn)
        hdr_lay.addStretch()

        # Language dropdown
        self.lang_select = LanguageSwitcher(is_dark=True)
        hdr_lay.addWidget(self.lang_select)
        hdr_lay.addSpacing(10)

        # theme toggle
        self.theme_toggle = ThemeToggle(is_dark=True)
        self.theme_toggle.toggled.connect(self._on_theme_toggle)
        hdr_lay.addWidget(self.theme_toggle)
        hdr_lay.addSpacing(20)
        return self.header


    def _build_footer(self) -> QFrame:
        ftr = QFrame()
        ftr.setObjectName("ConfigFooter")
        ftr.setFixedHeight(60)
        lay = QHBoxLayout(ftr)
        lay.setContentsMargins(24, 0, 24, 0)

        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("StatusLabel")
        lay.addWidget(self._status_lbl)
        lay.addStretch()

        load_btn = QPushButton("📂  Load JSON")
        load_btn.setObjectName("SecondaryBtn")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._on_load)
        lay.addWidget(load_btn)

        lay.addSpacing(12)

        save_btn = QPushButton("💾  Save Config")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        lay.addWidget(save_btn)

        return ftr

    # ── panels (lazy-init) ────────────────────────────────────────────────────
    def _ensure_panels(self):
        if hasattr(self, "_panels"):
            return
        tm = self._tm
        self._panels = {
            "display":  DisplayPanel(tm),
            "behavior": BehaviorPanel(tm),
            "header":   HeaderPanel(tm),
            "mapping":  MappingPanel(tm),
        }
        for panel in self._panels.values():
            self._panel_area.add(panel)

    # ── navigation ────────────────────────────────────────────────────────────
    def _switch_panel(self, key: str) -> None:
        self._ensure_panels()
        self._active_tab = key
        for k, panel in self._panels.items():
            panel.setVisible(k == key)
        # self._scroll.verticalScrollBar().setValue(0)

    # ── signals ───────────────────────────────────────────────────────────────
    def _connect_signals(self):
        pass

    def _on_theme_toggle(self, is_dark: bool):
        print(f"Theme toggled: is_dark={is_dark}")
        self._is_dark = is_dark
        self._tm.set_dark(is_dark)
        self._tm.apply(self)
        # Propagate to child panels
        if hasattr(self, "_panels"):
            for p in self._panels.values():
                self._tm.apply(p)
        # Update language switcher theme
        self.lang_select.set_theme(is_dark)
        self.back_btn.setStyleSheet((f"border: 1.5px solid {self._tm.color('border')};border-radius: 8px;"))
        log.info("Config theme toggled: is_dark=%s", is_dark)

    # ── I/O ──────────────────────────────────────────────────────────────────
    def _collect_config(self) -> dict:
        self._ensure_panels()
        return {
            "display":  self._panels["display"].get_values(),
            "behavior": self._panels["behavior"].get_values(),
            "header":   self._panels["header"].get_values(),
            "mapping":  self._panels["mapping"].get_values(),
        }

    def load_config(self, cfg: dict):
        self._ensure_panels()
        for key, panel in self._panels.items():
            if key in cfg:
                panel.set_values(cfg[key])

    def _on_save(self):
        from PySide6.QtWidgets import QFileDialog
        cfg = self._collect_config()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save config", "config.json", "JSON (*.json)"
        )
        if path:
            ok = ConfigIO.save(path, cfg)
            if ok:
                self._status_lbl.setText(f"✔  Saved → {path}")
                self.config_saved.emit(cfg)
            else:
                self._status_lbl.setText("✗  Save failed")

    def _on_load(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Load config", "", "JSON (*.json)"
        )
        if path:
            cfg = ConfigIO.load(path)
            if cfg:
                self.load_config(cfg)
                self._status_lbl.setText("✔  Config loaded")
            else:
                self._status_lbl.setText("✗  Could not load config")


# ── helper: stacked content without QStackedWidget ───────────────────────────
class QStackedContent(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self.setWidget(self._container)

    def add(self, widget: QWidget):
        self._layout.addWidget(widget)
        widget.hide()

    def show_panel(self, key: str, keys: list, panels: list):
        for k, p in zip(keys, panels):
            p.setVisible(k == key)
