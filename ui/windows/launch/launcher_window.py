

import json
import pathlib

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from core.app_state import get_state
from ui.themes.theme import THEMES, ThemeManager
from ui.windows.launch.view.modeCard import ModeCard
from ui.widgets.header import Header
from ui.windows.launch.view.styledDialog import StyledDialog

# Load modes list (static data — fine to read once at import)
_MODES_FILE = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "core" / "modes.json"
with open(_MODES_FILE, "r", encoding="utf-8") as _f:
    MODES = json.load(_f)


class MediaBridgeLauncher(QWidget):
    launch_requested = Signal(str)

    def __init__(self, parent=None, main_window:None=None):
        super().__init__()
        self.theme_name = "dark"
        self.selected_mode = None
        self._state = get_state()
        self._main_window = main_window
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

        # ── Header bar (shared widget) ──────────────────
        self._header = Header(
            show_back=False,
            show_kb_toggle=True,
            extra_buttons=[("Help", self._show_help), ("About", self._show_about)], main_window=self._main_window
        )
        self._header.theme_toggle.toggled.connect(self._on_theme_toggle)
        root_lay.addWidget(self._header)

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

        self.start_btn = QPushButton("Launch")
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

    def showEvent(self, event):
        """Sync theme and keyboard state when the page becomes visible again."""
        super().showEvent(event)
        self._header.sync_kb_state()
        if self._state.theme:
            is_dark = self._state.theme.is_dark
            new_theme = "dark" if is_dark else "light"
            if new_theme != self.theme_name:
                self.theme_name = new_theme
                for card in self.cards.values():
                    card.theme_name = self.theme_name
                    card.apply_theme()
                self.apply_theme()
        self._header.sync_theme()

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
        self.apply_theme()

    def apply_theme(self):
        t = self._get_colors()

        # hero
        self.hero_lbl.setStyleSheet(f"color: {t['text']};")
        self.sub_lbl.setStyleSheet(f"color: {t['text2']};")


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
        self._state.set_mode(mode_id)
        for mid, card in self.cards.items():
            card.set_selected(mid == mode_id)
        label = self._state.t(f"modes.{mode_id}.label")
        statusLbl = self._state.t('launch.mode_prefix') + " " + label
        self.status_lbl.setText(statusLbl)
        self.start_btn.setEnabled(True)
        self.apply_theme()

    def _on_launch(self):
        if not self.selected_mode:
            return
        self.launch_requested.emit(self.selected_mode)

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
        self.status_lbl.setText(self._state.t("launch.no_mode_selected"))
        self.start_btn.setText(self._state.t("launch.launch_btn"))
        label = self._state.t(f"modes.{self._state.selected_mode}.label")
        statusLbl = self._state.t('launch.mode_prefix') + " " + label
        self.status_lbl.setText(statusLbl)
