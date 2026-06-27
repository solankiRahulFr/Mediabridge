"""
Display Panel  –  fullscreen, resolution, orientation, background, colors.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QHBoxLayout,
    QColorDialog, QPushButton, QSizePolicy, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

from core.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from .base_panel import BasePanel


class ColorPicker(QWidget):
    """Compact color swatch + hex label that opens QColorDialog."""

    def __init__(self, default_hex: str = "#0D0F14",
                 parent: QWidget | None = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._btn = QPushButton()
        self._btn.setFixedSize(32, 32)
        self._btn.setObjectName("SmallBtn")
        self._btn.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self._btn)

        self._lbl = QLabel(default_hex)
        self._lbl.setObjectName("FieldLabel")
        lay.addWidget(self._lbl)
        lay.addStretch()

        self._color = QColor(default_hex)
        self._refresh_swatch()
        self._btn.clicked.connect(self._pick)

    def _pick(self):
        c = QColorDialog.getColor(self._color, self, "Pick Colour")
        if c.isValid():
            self._color = c
            self._lbl.setText(c.name())
            self._refresh_swatch()

    def _refresh_swatch(self):
        self._btn.setStyleSheet(
            f"background-color:{self._color.name()}; border-radius:6px; border:1px solid #444;"
        )

    def color_hex(self) -> str:
        return self._color.name()

    def set_color(self, hex_str: str):
        self._color = QColor(hex_str)
        self._lbl.setText(hex_str)
        self._refresh_swatch()


class DisplayPanel(BasePanel):
    def __init__(self, tm: ThemeManager, parent: QWidget | None = None):
        super().__init__(tm, parent)
        self._build()

    def _build(self):
        # ── Screen Setup ──────────────────────────────────────────────────────
        sec = self._section(
            "Screen Setup",
            "Configure display resolution, orientation and windowing behaviour.",
            title_key="config_dual_mode.display.screen_setup",
            desc_key="config_dual_mode.display.screen_setup.desc",
        )
        self.setStyleSheet("background-color: transparent;")  # for the colour preview swatches

        self._fullscreen = QCheckBox("")
        self._bind_text(self._fullscreen, "config_dual_mode.display.fullscreen_checkbox")
        self._fullscreen.setChecked(True)
        sec.addLayout(self._row("Fullscreen Mode", self._fullscreen,
                               label_key="config_dual_mode.display.fullscreen"))

        self._resolution = QComboBox()
        for r in ["3840×2160  (4K UHD)", "2560×1440  (QHD)",
                  "1920×1080  (FHD)", "1280×720  (HD)", "Auto-detect"]:
            self._resolution.addItem(r, r)
        self._bind_combobox_items(self._resolution, [
            "config_dual_mode.display.resolution_option_4k",
            "config_dual_mode.display.resolution_option_qhd",
            "config_dual_mode.display.resolution_option_fhd",
            "config_dual_mode.display.resolution_option_hd",
            "config_dual_mode.display.resolution_option_auto",
        ])
        sec.addLayout(self._row("Target Resolution", self._resolution,
                                "Ignored when fullscreen is on.",
                                label_key="config_dual_mode.display.resolution",
                                hint_key="config_dual_mode.display.resolution.hint"))

        self._orientation = QComboBox()
        for o in ["Landscape", "Portrait", "Landscape (flipped)", "Portrait (flipped)"]:
            self._orientation.addItem(o)
        self._bind_combobox_items(self._orientation, [
            "config_dual_mode.display.orientation.landscape",
            "config_dual_mode.display.orientation.portrait",
            "config_dual_mode.display.orientation.landscape_flipped",
            "config_dual_mode.display.orientation.portrait_flipped",
        ])
        sec.addLayout(self._row("Screen Orientation", self._orientation,
                               label_key="config_dual_mode.display.orientation"))

        self._control_screen = QComboBox()
        self._populate_screens(self._control_screen, default=0)
        sec.addLayout(self._row("Tactile Screen", self._control_screen,
                                "Which monitor for the touch/control window.",
                                label_key="config_dual_mode.display.control_screen",
                                hint_key="config_dual_mode.display.control_screen.hint"))

        self._display_screen = QComboBox()
        self._populate_screens(self._display_screen, default=1)
        sec.addLayout(self._row("Display Screen", self._display_screen,
                                "Which monitor for the 4K display output.",
                                label_key="config_dual_mode.display.display_screen",
                                hint_key="config_dual_mode.display.display_screen.hint"))

        # ── Colours ───────────────────────────────────────────────────────────
        csec = self._section(
            "Colour Overrides",
            "Override theme defaults per-deployment. Leave as theme default unless a brand kit is required.",
            title_key="config_dual_mode.display.colors",
            desc_key="config_dual_mode.display.colors.desc",
        )

        self._bg_color = ColorPicker("#0D0F14")
        csec.addLayout(self._row("Background Color", self._bg_color,
                                 label_key="config_dual_mode.display.bg_color",
                                 hint_key="config_dual_mode.display.bg_hint"))

        self._text_color = ColorPicker("#EEF0F8")
        csec.addLayout(self._row("Primary Text Color", self._text_color,
                                label_key="config_dual_mode.display.text_color"))

        self._accent_color = ColorPicker("#4F8EF7")
        csec.addLayout(self._row("Accent / Highlight Color", self._accent_color,
                                label_key="config_dual_mode.display.accent_color"))

        # ── Cursor ────────────────────────────────────────────────────────────
        cur_sec = self._section("Cursor & Touch",
                               title_key="config_dual_mode.display.cursor")

        self._hide_cursor = QCheckBox("")
        self._bind_text(self._hide_cursor, "config_dual_mode.display.hide_cursor_checkbox")
        self._hide_cursor.setChecked(True)
        cur_sec.addLayout(self._row("Cursor Visibility", self._hide_cursor,
                                   label_key="config_dual_mode.display.hide_cursor"))

        self._touch_ripple = QCheckBox("")
        self._bind_text(self._touch_ripple, "config_dual_mode.display.touch_ripple_checkbox")
        self._touch_ripple.setChecked(True)
        cur_sec.addLayout(self._row("Touch Feedback", self._touch_ripple,
                                   label_key="config_dual_mode.display.touch_ripple"))

        self._dpi_scale = QComboBox()
        for s in ["Auto", "100 %", "125 %", "150 %", "200 %"]:
            self._dpi_scale.addItem(s)
        self._bind_combobox_items(self._dpi_scale, [
            "config_dual_mode.display.dpi_scale.option_auto",
            "config_dual_mode.display.dpi_scale.option_100",
            "config_dual_mode.display.dpi_scale.option_125",
            "config_dual_mode.display.dpi_scale.option_150",
            "config_dual_mode.display.dpi_scale.option_200",
        ])
        cur_sec.addLayout(self._row("DPI Scale", self._dpi_scale,
                                    "Auto = let Qt decide based on screen DPI",
                                    label_key="config_dual_mode.display.dpi_scale",
                                    hint_key="config_dual_mode.display.dpi_scale.hint"))

        self._root.addStretch()
        
        # Apply initial translations
        self.retranslate_ui()

    # ── serialisation ─────────────────────────────────────────────────────────
    def get_values(self) -> dict:
        return {
            "fullscreen":    self._fullscreen.isChecked(),
            "resolution":    self._resolution.currentText(),
            "orientation":   self._orientation.currentText(),
            "control_screen": self._control_screen.currentData(),
            "display_screen": self._display_screen.currentData(),
            "bg_color":      self._bg_color.color_hex(),
            "text_color":    self._text_color.color_hex(),
            "accent_color":  self._accent_color.color_hex(),
            "hide_cursor":   self._hide_cursor.isChecked(),
            "touch_ripple":  self._touch_ripple.isChecked(),
            "dpi_scale":     self._dpi_scale.currentText(),
        }

    def set_values(self, d: dict):
        if "fullscreen"    in d: self._fullscreen.setChecked(d["fullscreen"])
        if "resolution"    in d: self._resolution.setCurrentText(d["resolution"])
        if "orientation"   in d: self._orientation.setCurrentText(d["orientation"])
        if "control_screen" in d: self._select_screen(self._control_screen, d["control_screen"])
        if "display_screen" in d: self._select_screen(self._display_screen, d["display_screen"])
        # backward compat: old single monitor_index → display_screen
        if "monitor_index" in d and "display_screen" not in d:
            self._select_screen(self._display_screen, d["monitor_index"])
        if "bg_color"      in d: self._bg_color.set_color(d["bg_color"])
        if "text_color"    in d: self._text_color.set_color(d["text_color"])
        if "accent_color"  in d: self._accent_color.set_color(d["accent_color"])
        if "hide_cursor"   in d: self._hide_cursor.setChecked(d["hide_cursor"])
        if "touch_ripple"  in d: self._touch_ripple.setChecked(d["touch_ripple"])
        if "dpi_scale"     in d: self._dpi_scale.setCurrentText(d["dpi_scale"])

    def retranslate_ui(self) -> None:
        """Update translatable strings."""
        super().retranslate_ui()  # Call parent to update all bound labels

    # ── screen helpers ────────────────────────────────────────────────────────
    def _populate_screens(self, combo: QComboBox, default: int = 0) -> None:
        """Fill a QComboBox with detected screens (index + name + resolution)."""
        combo.clear()
        screens = QGuiApplication.screens()
        for i, scr in enumerate(screens):
            geo = scr.geometry()
            label = f"Screen {i}: {scr.name()}  ({geo.width()}×{geo.height()})"
            combo.addItem(label, i)
        # Select the requested default (clamped)
        idx = min(default, len(screens) - 1) if screens else 0
        combo.setCurrentIndex(idx)

    @staticmethod
    def _select_screen(combo: QComboBox, screen_idx: int) -> None:
        """Select a screen by its index value (stored as item data)."""
        for i in range(combo.count()):
            if combo.itemData(i) == screen_idx:
                combo.setCurrentIndex(i)
                return

    def refresh_screens(self) -> None:
        """Re-detect screens — call when screen config may have changed."""
        ctrl_val = self._control_screen.currentData() or 0
        disp_val = self._display_screen.currentData() or 1
        self._populate_screens(self._control_screen, ctrl_val)
        self._populate_screens(self._display_screen, disp_val)

