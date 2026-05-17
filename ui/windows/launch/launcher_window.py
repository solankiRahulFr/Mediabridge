"""
Launcher / mode-selection screen — the first thing the user sees.

All colour tokens come from ``get_state().theme`` (central ThemeManager).
All translations come from ``get_state().lang`` (central LanguageManager).
No direct JSON file reads.
"""

import json
import pathlib

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QPixmap

from core.app_state import get_state
from ui.themes.theme import THEMES, ThemeManager
from ui.windows.launch.view.modeCard import ModeCard
from ui.widgets.togglebutton import ThemeToggle
from ui.windows.launch.view.styledDialog import StyledDialog
from ui.widgets.language_switcher import LanguageSwitcher

# Load modes list (static data — fine to read once at import)
_MODES_FILE = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "core" / "modes.json"
with open(_MODES_FILE, "r", encoding="utf-8") as _f:
    MODES = json.load(_f)


class MediaBridgeLauncher(QWidget):
    launch_requested = Signal()

    def __init__(self, parent=None):
        super().__init__()
        self.theme_name = "dark"
        self.selected_mode = None
        self._state = get_state()
        self._build_ui()
        self.apply_theme()

    def _get_colors(self) -> dict[str, str]:
        if self._state.theme:
            return self._state.theme.colors
        return THEMES[self.theme_name]

    # ── build ──────────────────────────────────
    def _build_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── Header bar ──────────────────
        self.header = QWidget()
        self.header.setFixedHeight(64)
        hdr_lay = QHBoxLayout(self.header)
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
        # logo_lbl = QLabel("MediaBridge")
        logo_font = QFont(); logo_font.setPointSize(13); logo_font.setWeight(QFont.Bold)
        logo_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        # logo_lbl.setFont(logo_font)
        # self.logo_lbl = logo_lbl
        hdr_lay.addWidget(logo_image)
        # hdr_lay.addWidget(logo_lbl)
        hdr_lay.addStretch()

        # Language dropdown
        self.lang_select = LanguageSwitcher(is_dark=True)
        hdr_lay.addWidget(self.lang_select)
        hdr_lay.addSpacing(20)

        # theme toggle
        self.theme_toggle = ThemeToggle(is_dark=True)
        self.theme_toggle.toggled.connect(self._on_theme_toggle)
        hdr_lay.addWidget(self.theme_toggle)
        hdr_lay.addSpacing(20)

        # Help / About
        for label, slot in [("Help", self._show_help), ("About", self._show_about)]:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setFixedWidth(72)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            bf = QFont(); bf.setPointSize(9); bf.setWeight(QFont.Medium)
            btn.setFont(bf)
            btn.clicked.connect(slot)
            hdr_lay.addWidget(btn)
            hdr_lay.addSpacing(8)
            if label == "Help":
                self.help_btn = btn
            else:
                self.about_btn = btn

        root_lay.addWidget(self.header)

        # ── Body ─────────────────────────
        self.body = QWidget()
        body_lay = QVBoxLayout(self.body)
        body_lay.setContentsMargins(48, 36, 48, 20)
        body_lay.setSpacing(0)

        # Hero text
        hero = QLabel(self._state.t("launch.select_mode"))
        hf = QFont(); hf.setPointSize(26); hf.setWeight(QFont.Bold)
        hero.setFont(hf)
        self.hero_lbl = hero
        body_lay.addWidget(hero)

        sub = QLabel(self._state.t("launch.choose_mode"))
        sub.setWordWrap(True)
        sf = QFont(); sf.setPointSize(11)
        sub.setFont(sf)
        self.sub_lbl = sub
        body_lay.addWidget(sub)
        body_lay.addSpacing(32)

        # Mode cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.cards: dict[str, ModeCard] = {}
        for m in MODES:
            card = ModeCard(m, self.theme_name, self)
            card.selected.connect(self._on_mode_selected)
            self.cards[m["id"]] = card
            cards_row.addWidget(card)
        body_lay.addLayout(cards_row)

        body_lay.addStretch()

        # ── Bottom bar ───────────────────
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        self.status_lbl = QLabel("No mode selected")
        self.status_lbl.setFont(QFont())
        bottom_bar.addWidget(self.status_lbl)
        bottom_bar.addStretch()

        self.start_btn = QPushButton("  Launch  →")
        start_font = QFont(); start_font.setPointSize(12); start_font.setWeight(QFont.DemiBold)
        self.start_btn.setFont(start_font)
        self.start_btn.setFixedHeight(48)
        self.start_btn.setMinimumWidth(160)
        self.start_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._on_launch)
        bottom_bar.addWidget(self.start_btn)

        body_lay.addLayout(bottom_bar)
        body_lay.addSpacing(8)
        root_lay.addWidget(self.body, 1)

        # Subscribe to language changes
        self._state.lang.on_change(lambda _code: self.retranslate_ui())

    # ── Theme ──────────────────────────────────
    def _on_theme_toggle(self, is_dark: bool):
        self.theme_name = "dark" if is_dark else "light"
        # Update central ThemeManager
        if self._state.theme:
            self._state.theme.set_dark(is_dark)
        # Notify AppState observers about the global theme change
        try:
            self._state.set("is_dark", is_dark)
        except Exception:
            pass
        for card in self.cards.values():
            card.theme_name = self.theme_name
            card.apply_theme()
        self.lang_select.set_theme(is_dark)
        self.apply_theme()

    def apply_theme(self):
        t = self._get_colors()

        self.setStyleSheet(f"QMainWindow {{ background: {t['bg']}; }}")

        # header
        self.header.setStyleSheet(
            f"background: {t['bg2']}; border-bottom: 1px solid {t['border']};"
        )
        # self.logo_lbl.setStyleSheet(f"color: {t['accent']};")

        # hero
        self.hero_lbl.setStyleSheet(f"color: {t['text']};")
        self.sub_lbl.setStyleSheet(f"color: {t['text2']};")

        # help / about
        ghost_style = (
            f"QPushButton {{ background: transparent; color: {t['text2']}; "
            f"border: 1.5px solid {t['border']}; border-radius: 8px; }}"
            f"QPushButton:hover {{ color: {t['text']}; border-color: {t['accent']}; }}"
        )
        self.help_btn.setStyleSheet(ghost_style)
        self.about_btn.setStyleSheet(ghost_style)

        # status
        self.status_lbl.setStyleSheet(f"color: {t['text3']}; font-size: 10pt;")

        # launch button
        if self.start_btn.isEnabled():
            self.start_btn.setStyleSheet(
                f"QPushButton {{ background: qlineargradient("
                f"x1:0,y1:0,x2:1,y2:0, stop:0 {t['accent']}, stop:1 {t['accent2']}); "
                f"color: #fff; border: none; border-radius: 12px; padding: 0 28px; }}"
                f"QPushButton:hover {{ opacity: 0.85; }}"
            )
        else:
            self.start_btn.setStyleSheet(
                f"QPushButton {{ background: {t['surface2']}; color: {t['text3']}; "
                f"border: 1.5px solid {t['border']}; border-radius: 12px; padding: 0 28px; }}"
            )

        self.body.setStyleSheet(f"background: {t['bg']};")

    # ── Slots ──────────────────────────────────
    def _on_mode_selected(self, mode_id: str):
        self.selected_mode = mode_id
        for mid, card in self.cards.items():
            card.set_selected(mid == mode_id)
        label = self._state.t(f"modes.{mode_id}.label")
        self.status_lbl.setText(f"{self._state.t('launch.mode_prefix')} {label}")
        self.start_btn.setEnabled(True)
        self.apply_theme()

    def _on_launch(self):
        if not self.selected_mode:
            return
        self.launch_requested.emit()

    def _show_help(self):
        dlg = StyledDialog(
            "Help",
            """
            <b>Getting started</b><br><br>
            1. Choose a <b>Display Mode</b> that matches your hardware setup.<br><br>
            2. Click <b>Launch →</b> to start the kiosk session.<br><br>
            <b>Modes at a glance</b><br>
            &nbsp;· <b>Dual Screen</b> — tactile control + separate 4K output<br>
            &nbsp;· <b>Display Only</b> — single screen for media or web<br>
            &nbsp;· <b>Control + View</b> — touch screen for both nav and media<br><br>
            <b>Media supported:</b> PDF, PPT/PPTX, Images, Video<br>
            <b>Controls:</b> pinch-to-zoom, slide navigation, video playback
            """,
            self.theme_name,
            self,
        )
        dlg.exec()

    def _show_about(self):
        dlg = StyledDialog(
            "About MediaBridge",
            """
            <b>MediaBridge</b> v1.0.0<br><br>
            A professional multi-screen kiosk platform for presentations,<br>
            digital signage, and interactive media.<br><br>
            Built with <b>PySide6</b> · Python 3.11+<br><br>
            <i>Supports PDF · PPT · Images · Video · Web pages</i><br><br>
            © 2026 Your Company. All rights reserved.
            """,
            self.theme_name,
            self,
        )
        dlg.exec()

    def retranslate_ui(self):
        self.hero_lbl.setText(self._state.t("launch.select_mode"))
        self.sub_lbl.setText(self._state.t("launch.choose_mode"))
        self.help_btn.setText(self._state.t("header.help"))
        self.about_btn.setText(self._state.t("header.about"))
        self.status_lbl.setText(self._state.t("launch.no_mode_selected"))
        self.start_btn.setText(self._state.t("launch.launch_btn"))
