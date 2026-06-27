"""
Two tabs:
  1. Media  — configure local/remote media sources
  2. Restaurant — configure menu source, restaurant branding, display settings
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSpinBox, QStackedWidget,
    QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont, QGuiApplication

from core.app_state import get_state
from core.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from core.configio import ConfigIO
from ui.widgets.header import Header
from ui.widgets.navbar import NavTabs

log = logging.getLogger(__name__)


class ConfigWindowControl(I18nMixin, QWidget):
    back_requested = Signal()
    launch_requested = Signal(dict)

    def __init__(self, parent: QWidget | None = None, is_dark: bool = True):
        super().__init__(parent)
        self._state = get_state()
        self._is_dark = self._state.theme.is_dark if self._state.theme else is_dark

        if self._state.theme:
            self._tm = self._state.theme
        else:
            self._tm = ThemeManager(self._is_dark)

        self._active_tab = "media"
        self._build()
        self._header.theme_toggle.toggled.connect(self._on_theme_toggle)
        self._state.lang.on_change(lambda _: self.retranslate_ui())
        self._tm.apply(self)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        # Tabs
        self.tabs = NavTabs(
            tabs=[("media", "Media Viewer"), ("restaurant", "Restaurant")],
            tm=self._tm,
        )
        self.tabs.tab_changed.connect(self._switch_tab)
        root.addWidget(self.tabs)

        # Content area
        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setFrameShape(QFrame.NoFrame)

        self._media_panel = self._build_media_panel()
        self._restaurant_panel = self._build_restaurant_panel()

        self._tab_stack = QStackedWidget()
        self._tab_stack.addWidget(self._media_panel)       # index 0
        self._tab_stack.addWidget(self._restaurant_panel)  # index 1
        self._content_scroll.setWidget(self._tab_stack)

        root.addWidget(self._content_scroll, 1)

        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        self._header = Header(show_back=True)
        self._header.back_requested.connect(self.back_requested.emit)
        return self._header

    # ── Media Panel ───────────────────────────────────────────────

    def _build_media_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(32, 20, 32, 20)
        lay.setSpacing(16)

        lay.addWidget(self._section_title("Media Sources"))

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Local folder:"))
        self._media_local_dir = QLineEdit()
        self._media_local_dir.setPlaceholderText("/path/to/media/folder")
        row1.addWidget(self._media_local_dir, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SecondaryBtn")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_media_dir)
        row1.addWidget(browse_btn)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Remote URL:"))
        self._media_remote_url = QLineEdit()
        self._media_remote_url.setPlaceholderText("https://api.example.com/content")
        row2.addWidget(self._media_remote_url, 1)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Auth header:"))
        self._media_header_key = QLineEdit()
        self._media_header_key.setPlaceholderText("Authorization")
        self._media_header_key.setFixedWidth(140)
        row3.addWidget(self._media_header_key)
        self._media_header_val = QLineEdit()
        self._media_header_val.setPlaceholderText("Bearer token…")
        row3.addWidget(self._media_header_val, 1)
        lay.addLayout(row3)

        # ── Screen selection ──────────────────────────────────────
        lay.addWidget(self._section_title("Target Screen"))

        row_screen = QHBoxLayout()
        row_screen.addWidget(QLabel("Display on:"))
        self._media_screen = QComboBox()
        self._populate_screens(self._media_screen, default=0)
        self._media_screen.setMinimumWidth(220)
        row_screen.addWidget(self._media_screen)
        row_screen.addStretch()
        lay.addLayout(row_screen)

        # ── Screensaver ───────────────────────────────────────────
        lay.addWidget(self._section_title("Screensaver"))

        row_ss_type = QHBoxLayout()
        row_ss_type.addWidget(QLabel("Type:"))
        self._media_ss_type = QComboBox()
        self._media_ss_type.addItems(["dim", "image", "video"])
        self._media_ss_type.setFixedWidth(100)
        row_ss_type.addWidget(self._media_ss_type)
        row_ss_type.addSpacing(16)
        row_ss_type.addWidget(QLabel("Timeout (seconds):"))
        self._media_ss_timeout = QSpinBox()
        self._media_ss_timeout.setRange(10, 3600)
        self._media_ss_timeout.setValue(120)
        self._media_ss_timeout.setFixedWidth(80)
        row_ss_type.addWidget(self._media_ss_timeout)
        row_ss_type.addStretch()
        lay.addLayout(row_ss_type)

        row_ss_src = QHBoxLayout()
        row_ss_src.addWidget(QLabel("Source:"))
        self._media_ss_source = QLineEdit()
        self._media_ss_source.setPlaceholderText("/path/to/screensaver image or video")
        row_ss_src.addWidget(self._media_ss_source, 1)
        ss_browse = QPushButton("Browse")
        ss_browse.setObjectName("SecondaryBtn")
        ss_browse.setCursor(Qt.PointingHandCursor)
        ss_browse.clicked.connect(self._browse_media_screensaver)
        row_ss_src.addWidget(ss_browse)
        lay.addLayout(row_ss_src)

        lay.addStretch()
        return panel

    # ── Restaurant Panel ──────────────────────────────────────────

    def _build_restaurant_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(32, 20, 32, 20)
        lay.setSpacing(16)

        # Branding
        lay.addWidget(self._section_title("Restaurant Branding"))

        row_name = QHBoxLayout()
        row_name.addWidget(QLabel("Restaurant name:"))
        self._rest_name = QLineEdit()
        self._rest_name.setPlaceholderText("My Restaurant")
        row_name.addWidget(self._rest_name, 1)
        lay.addLayout(row_name)

        row_logo = QHBoxLayout()
        row_logo.addWidget(QLabel("Logo:"))
        self._rest_logo = QLineEdit()
        self._rest_logo.setPlaceholderText("/path/to/logo.png")
        row_logo.addWidget(self._rest_logo, 1)
        logo_browse = QPushButton("Browse")
        logo_browse.setObjectName("SecondaryBtn")
        logo_browse.setCursor(Qt.PointingHandCursor)
        logo_browse.clicked.connect(self._browse_logo)
        row_logo.addWidget(logo_browse)
        lay.addLayout(row_logo)

        # Display config
        lay.addWidget(self._section_title("Display Config"))

        row_hdr_bg = QHBoxLayout()
        row_hdr_bg.addWidget(QLabel("Header background:"))
        self._rest_hdr_bg = QLineEdit("#1A1D23")
        self._rest_hdr_bg.setFixedWidth(100)
        row_hdr_bg.addWidget(self._rest_hdr_bg)
        row_hdr_bg.addSpacing(20)
        row_hdr_bg.addWidget(QLabel("Header text:"))
        self._rest_hdr_color = QLineEdit("#FFFFFF")
        self._rest_hdr_color.setFixedWidth(100)
        row_hdr_bg.addWidget(self._rest_hdr_color)
        row_hdr_bg.addStretch()
        lay.addLayout(row_hdr_bg)

        row_btn = QHBoxLayout()
        row_btn.addWidget(QLabel("Button color (accent):"))
        self._rest_accent = QLineEdit("#6C63FF")
        self._rest_accent.setFixedWidth(100)
        row_btn.addWidget(self._rest_accent)
        row_btn.addStretch()
        lay.addLayout(row_btn)

        # Screensaver
        lay.addWidget(self._section_title("Screensaver"))

        row_ss = QHBoxLayout()
        row_ss.addWidget(QLabel("Type:"))
        self._rest_ss_type = QComboBox()
        self._rest_ss_type.addItems(["none", "image", "video"])
        self._rest_ss_type.setFixedWidth(100)
        row_ss.addWidget(self._rest_ss_type)
        row_ss.addSpacing(12)
        row_ss.addWidget(QLabel("Source:"))
        self._rest_ss_source = QLineEdit()
        self._rest_ss_source.setPlaceholderText("/path/to/screensaver.mp4")
        row_ss.addWidget(self._rest_ss_source, 1)
        ss_browse = QPushButton("Browse")
        ss_browse.setObjectName("SecondaryBtn")
        ss_browse.setCursor(Qt.PointingHandCursor)
        ss_browse.clicked.connect(self._browse_screensaver)
        row_ss.addWidget(ss_browse)
        lay.addLayout(row_ss)

        # Menu data
        lay.addWidget(self._section_title("Menu Data"))

        row_menu = QHBoxLayout()
        row_menu.addWidget(QLabel("Menu file (JSON/CSV):"))
        self._rest_menu_source = QLineEdit()
        self._rest_menu_source.setPlaceholderText("/path/to/menu.json or menu.csv")
        row_menu.addWidget(self._rest_menu_source, 1)
        menu_browse = QPushButton("Browse")
        menu_browse.setObjectName("SecondaryBtn")
        menu_browse.setCursor(Qt.PointingHandCursor)
        menu_browse.clicked.connect(self._browse_menu)
        row_menu.addWidget(menu_browse)
        lay.addLayout(row_menu)

        lay.addStretch()
        return panel

    # ── Footer ────────────────────────────────────────────────────

    def _build_footer(self) -> QFrame:
        ftr = QFrame()
        ftr.setObjectName("ConfigFooter")
        ftr.setFixedHeight(60)
        lay = QHBoxLayout(ftr)
        lay.setContentsMargins(24, 0, 24, 0)

        self._status_lbl = QLabel("")
        lay.addWidget(self._status_lbl)
        lay.addStretch()

        load_btn = QPushButton("Load Config")
        load_btn.setObjectName("SecondaryBtn")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._on_load)
        lay.addWidget(load_btn)
        lay.addSpacing(8)

        save_btn = QPushButton("Save Config")
        save_btn.setObjectName("SecondaryBtn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        lay.addWidget(save_btn)
        lay.addSpacing(12)

        launch_btn = QPushButton("Launch")
        launch_btn.setCursor(Qt.PointingHandCursor)
        launch_btn.setObjectName("PrimaryBtn")
        # launch_btn.setStyleSheet(
        #     f"QPushButton {{ background: {self._tm.color('accent')}; color: #fff; "
        #     f"border: none; border-radius: 8px; padding: 8px 20px; font-weight: bold; }}"
        #     f"QPushButton:hover {{ background: {self._tm.color('accent2')}; }}"
        # )
        launch_btn.clicked.connect(self._on_launch)
        lay.addWidget(launch_btn)

        return ftr

    # ── Helpers ───────────────────────────────────────────────────

    def _section_title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        font = QFont()
        font.setPointSize(12)
        font.setWeight(QFont.Bold)
        lbl.setFont(font)
        lbl.setStyleSheet(f"color: {self._tm.color('text')}; padding-top: 8px;")
        return lbl

    def _switch_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        if tab_id == "media":
            self._tab_stack.setCurrentIndex(0)
        else:
            self._tab_stack.setCurrentIndex(1)

    # ── Browse dialogs ────────────────────────────────────────────

    def _browse_media_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Media Folder")
        if path:
            self._media_local_dir.setText(path)

    def _browse_media_screensaver(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Screensaver", "",
            "Media (*.mp4 *.jpg *.png *.webm *.gif)"
        )
        if path:
            self._media_ss_source.setText(path)

    def _browse_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", "Images (*.png *.jpg *.svg)"
        )
        if path:
            self._rest_logo.setText(path)

    def _browse_screensaver(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Screensaver", "",
            "Media (*.mp4 *.jpg *.png *.webm *.gif)"
        )
        if path:
            self._rest_ss_source.setText(path)

    def _browse_menu(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Menu File", "", "Data (*.json *.csv)"
        )
        if path:
            self._rest_menu_source.setText(path)

    def _populate_screens(self, combo: QComboBox, default: int = 0) -> None:
        combo.clear()
        screens = QGuiApplication.screens()
        for i, scr in enumerate(screens):
            geo = scr.geometry()
            label = f"Screen {i}: {scr.name()}  ({geo.width()}×{geo.height()})"
            combo.addItem(label, i)
        idx = min(default, len(screens) - 1) if screens else 0
        combo.setCurrentIndex(idx)

    # ── Collect / Apply ───────────────────────────────────────────

    def _collect_config(self) -> dict:
        return {
            "sub_mode": self._active_tab,
            "screen_index": self._media_screen.currentData(),
            "media": {
                "local_dir": self._media_local_dir.text().strip(),
                "remote_url": self._media_remote_url.text().strip(),
                "remote_headers": {
                    self._media_header_key.text().strip():
                    self._media_header_val.text().strip()
                } if self._media_header_key.text().strip() else {},
                "screensaver": {
                    "type": self._media_ss_type.currentText(),
                    "source": self._media_ss_source.text().strip(),
                    "timeout_seconds": self._media_ss_timeout.value(),
                },
            },
            "restaurant": {
                "restaurant_name": self._rest_name.text().strip(),
                "logo_url": self._rest_logo.text().strip(),
                "header_bg": self._rest_hdr_bg.text().strip(),
                "header_color": self._rest_hdr_color.text().strip(),
                "accent_color": self._rest_accent.text().strip(),
                "screensaver": {
                    "type": self._rest_ss_type.currentText(),
                    "source": self._rest_ss_source.text().strip(),
                    "loop": True,
                },
                "menu_source": self._rest_menu_source.text().strip(),
            },
        }

    def load_config(self, cfg: dict) -> None:
        media = cfg.get("media", {})
        self._media_local_dir.setText(media.get("local_dir", ""))
        self._media_remote_url.setText(media.get("remote_url", ""))
        headers = media.get("remote_headers", {})
        if headers:
            key = next(iter(headers), "")
            self._media_header_key.setText(key)
            self._media_header_val.setText(headers.get(key, ""))

        # Screen selection
        screen_idx = cfg.get("screen_index", 0)
        for i in range(self._media_screen.count()):
            if self._media_screen.itemData(i) == screen_idx:
                self._media_screen.setCurrentIndex(i)
                break

        # Media screensaver
        media_ss = media.get("screensaver", {})
        idx_ss = self._media_ss_type.findText(media_ss.get("type", "dim"))
        if idx_ss >= 0:
            self._media_ss_type.setCurrentIndex(idx_ss)
        self._media_ss_source.setText(media_ss.get("source", ""))
        self._media_ss_timeout.setValue(media_ss.get("timeout_seconds", 120))

        rest = cfg.get("restaurant", {})
        self._rest_name.setText(rest.get("restaurant_name", ""))
        self._rest_logo.setText(rest.get("logo_url", ""))
        self._rest_hdr_bg.setText(rest.get("header_bg", "#1A1D23"))
        self._rest_hdr_color.setText(rest.get("header_color", "#FFFFFF"))
        self._rest_accent.setText(rest.get("accent_color", "#6C63FF"))

        ss = rest.get("screensaver", {})
        idx = self._rest_ss_type.findText(ss.get("type", "none"))
        if idx >= 0:
            self._rest_ss_type.setCurrentIndex(idx)
        self._rest_ss_source.setText(ss.get("source", ""))
        self._rest_menu_source.setText(rest.get("menu_source", ""))

        sub = cfg.get("sub_mode", "media")
        self._switch_tab(sub)
        self.tabs.set_active(sub)

    # ── Actions ───────────────────────────────────────────────────

    def _on_save(self) -> None:
        cfg = self._collect_config()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Config", "mediaBridge_Control_config.json", "JSON (*.json)"
        )
        if path:
            if ConfigIO.save(path, cfg):
                self._status_lbl.setText(f"✔  Saved → {path}")
            else:
                self._status_lbl.setText("✗  Save failed")

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Config", "", "JSON (*.json)"
        )
        if path:
            cfg = ConfigIO.load(path)
            if cfg:
                self.load_config(cfg)
                self._status_lbl.setText("✔  Config loaded")
            else:
                self._status_lbl.setText("✗  Could not load config")

    def _on_launch(self) -> None:
        cfg = self._collect_config()
        self._state.apply_config({"control": cfg})
        self.launch_requested.emit(cfg)

    # ── Theme ─────────────────────────────────────────────────────

    def _on_theme_toggle(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self._tm.set_dark(is_dark)
        self._state.set("is_dark", is_dark)
        self._tm.apply(self)

    def showEvent(self, event):
        super().showEvent(event)
        if self._state.theme:
            is_dark = self._state.theme.is_dark
            if is_dark != self._is_dark:
                self._is_dark = is_dark
                self._tm.set_dark(is_dark)
                self._tm.apply(self)
        self._header.sync_theme()

    def retranslate_ui(self) -> None:
        I18nMixin._do_retranslate(self)

