"""
Display Panel  –  fullscreen, resolution, orientation, background, colors.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QHBoxLayout,
    QColorDialog, QPushButton, QSizePolicy, QSpinBox, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from core.base_panel import BasePanel
from core.theme import ThemeManager


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
        )

        self._fullscreen = QCheckBox("Launch in fullscreen")
        self._fullscreen.setChecked(True)
        sec.addLayout(self._row("Fullscreen Mode", self._fullscreen)[0])

        self._resolution = QComboBox()
        for r in ["3840×2160  (4K UHD)", "2560×1440  (QHD)",
                  "1920×1080  (FHD)", "1280×720  (HD)", "Auto-detect"]:
            self._resolution.addItem(r)
        sec.addLayout(self._row("Target Resolution", self._resolution,
                                "Ignored when fullscreen is on.")[0])

        self._orientation = QComboBox()
        for o in ["Landscape", "Portrait", "Landscape (flipped)", "Portrait (flipped)"]:
            self._orientation.addItem(o)
        sec.addLayout(self._row("Screen Orientation", self._orientation)[0])

        self._monitor_idx = QSpinBox()
        self._monitor_idx.setRange(0, 7)
        self._monitor_idx.setSuffix("  (0 = primary)")
        sec.addLayout(self._row("Monitor Index", self._monitor_idx,
                                "Multi-display: 0 = primary screen")[0])

        # ── Colours ───────────────────────────────────────────────────────────
        csec = self._section(
            "Colour Overrides",
            "Override theme defaults per-deployment. Leave as theme default unless a brand kit is required.",
        )

        self._bg_color = ColorPicker("#0D0F14")
        csec.addLayout(self._row("Background Color", self._bg_color,
                                 "Main application background")[0])

        self._text_color = ColorPicker("#EEF0F8")
        csec.addLayout(self._row("Primary Text Color", self._text_color)[0])

        self._accent_color = ColorPicker("#4F8EF7")
        csec.addLayout(self._row("Accent / Highlight Color", self._accent_color)[0])

        # ── Cursor ────────────────────────────────────────────────────────────
        cur_sec = self._section("Cursor & Touch")

        self._hide_cursor = QCheckBox("Hide mouse cursor (touch-only mode)")
        self._hide_cursor.setChecked(True)
        cur_sec.addLayout(self._row("Cursor Visibility", self._hide_cursor)[0])

        self._touch_ripple = QCheckBox("Show touch ripple animation")
        self._touch_ripple.setChecked(True)
        cur_sec.addLayout(self._row("Touch Feedback", self._touch_ripple)[0])

        self._dpi_scale = QComboBox()
        for s in ["Auto", "100 %", "125 %", "150 %", "200 %"]:
            self._dpi_scale.addItem(s)
        cur_sec.addLayout(self._row("DPI Scale", self._dpi_scale,
                                    "Auto = let Qt decide based on screen DPI")[0])

        self._root.addStretch()

    # ── serialisation ─────────────────────────────────────────────────────────
    def get_values(self) -> dict:
        return {
            "fullscreen":    self._fullscreen.isChecked(),
            "resolution":    self._resolution.currentText(),
            "orientation":   self._orientation.currentText(),
            "monitor_index": self._monitor_idx.value(),
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
        if "monitor_index" in d: self._monitor_idx.setValue(d["monitor_index"])
        if "bg_color"      in d: self._bg_color.set_color(d["bg_color"])
        if "text_color"    in d: self._text_color.set_color(d["text_color"])
        if "accent_color"  in d: self._accent_color.set_color(d["accent_color"])
        if "hide_cursor"   in d: self._hide_cursor.setChecked(d["hide_cursor"])
        if "touch_ripple"  in d: self._touch_ripple.setChecked(d["touch_ripple"])
        if "dpi_scale"     in d: self._dpi_scale.setCurrentText(d["dpi_scale"])
