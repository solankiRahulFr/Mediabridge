"""
Header Panel  –  show/hide, logo URL, title text, position, branding colours.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit,
    QSpinBox, QWidget,
)
from core.base_panel import BasePanel
from core.theme import ThemeManager
from .display_panel import ColorPicker


class HeaderPanel(BasePanel):
    def __init__(self, tm: ThemeManager, parent: QWidget | None = None):
        super().__init__(tm, parent)
        self._build()

    def _build(self):
        # ── Visibility ────────────────────────────────────────────────────────
        sec = self._section(
            "Header Visibility",
            "The header bar appears at the top of the kiosk UI. "
            "It can carry branding, a clock, or navigation controls.",
        )

        self._show_header = QCheckBox("Show header bar")
        self._show_header.setChecked(True)
        sec.addLayout(self._row("Header Visible", self._show_header)[0])

        self._header_height = QSpinBox()
        self._header_height.setRange(40, 200)
        self._header_height.setValue(64)
        self._header_height.setSuffix("  px")
        sec.addLayout(self._row("Header Height", self._header_height)[0])

        self._header_bg = ColorPicker("#13161E")
        sec.addLayout(self._row("Header Background", self._header_bg)[0])

        self._header_text_color = ColorPicker("#EEF0F8")
        sec.addLayout(self._row("Header Text Color", self._header_text_color)[0])

        # ── Title ─────────────────────────────────────────────────────────────
        tsec = self._section("Title")

        self._show_title = QCheckBox("Show title in header")
        self._show_title.setChecked(True)
        tsec.addLayout(self._row("Show Title", self._show_title)[0])

        self._title_text = QLineEdit()
        self._title_text.setPlaceholderText("e.g. Museum Gallery  ·  Conference Kiosk")
        tsec.addLayout(self._row("Title Text", self._title_text)[0])

        self._title_font_size = QSpinBox()
        self._title_font_size.setRange(10, 72)
        self._title_font_size.setValue(18)
        self._title_font_size.setSuffix("  pt")
        tsec.addLayout(self._row("Title Font Size", self._title_font_size)[0])

        self._title_position = QComboBox()
        for p in ["Left", "Centre", "Right"]:
            self._title_position.addItem(p)
        tsec.addLayout(self._row("Title Position", self._title_position)[0])

        # ── Logo ──────────────────────────────────────────────────────────────
        lsec = self._section(
            "Logo",
            "Supports local file paths and remote URLs. "
            "SVG is recommended for crisp 4K rendering.",
        )

        self._show_logo = QCheckBox("Show logo in header")
        self._show_logo.setChecked(True)
        lsec.addLayout(self._row("Show Logo", self._show_logo)[0])

        self._logo_url = QLineEdit()
        self._logo_url.setPlaceholderText("/assets/logo.svg  or  https://example.com/logo.png")
        lsec.addLayout(self._row("Logo URL / Path", self._logo_url)[0])

        self._logo_position = QComboBox()
        for p in ["Left", "Right", "Centre"]:
            self._logo_position.addItem(p)
        lsec.addLayout(self._row("Logo Position", self._logo_position)[0])

        self._logo_height = QSpinBox()
        self._logo_height.setRange(16, 160)
        self._logo_height.setValue(40)
        self._logo_height.setSuffix("  px")
        lsec.addLayout(self._row("Logo Max Height", self._logo_height)[0])

        self._logo_clickable = QCheckBox(
            "Logo is the exit gesture target  (requires Behavior → exit taps)"
        )
        lsec.addLayout(self._row("Logo as Exit Target", self._logo_clickable,
                                 "Users must tap the logo N times to unlock kiosk mode")[0])

        # ── Extras ────────────────────────────────────────────────────────────
        xsec = self._section("Header Extras")

        self._show_clock = QCheckBox("Show live clock")
        xsec.addLayout(self._row("Clock", self._show_clock)[0])

        self._clock_format = QComboBox()
        for f in ["HH:MM", "HH:MM:SS", "HH:MM  (12h AM/PM)", "Day, DD MMM YYYY  HH:MM"]:
            self._clock_format.addItem(f)
        xsec.addLayout(self._row("Clock Format", self._clock_format)[0])

        self._show_lang = QCheckBox("Show language switcher in header")
        self._show_lang.setChecked(True)
        xsec.addLayout(self._row("Language Switcher", self._show_lang)[0])

        self._show_theme_toggle = QCheckBox("Show dark/light theme toggle in header")
        xsec.addLayout(self._row("Theme Toggle", self._show_theme_toggle)[0])

        self._root.addStretch()

    # ── serialisation ─────────────────────────────────────────────────────────
    def get_values(self) -> dict:
        return {
            "show_header":       self._show_header.isChecked(),
            "header_height":     self._header_height.value(),
            "header_bg":         self._header_bg.color_hex(),
            "header_text_color": self._header_text_color.color_hex(),
            "show_title":        self._show_title.isChecked(),
            "title_text":        self._title_text.text().strip(),
            "title_font_size":   self._title_font_size.value(),
            "title_position":    self._title_position.currentText(),
            "show_logo":         self._show_logo.isChecked(),
            "logo_url":          self._logo_url.text().strip(),
            "logo_position":     self._logo_position.currentText(),
            "logo_height":       self._logo_height.value(),
            "logo_clickable":    self._logo_clickable.isChecked(),
            "show_clock":        self._show_clock.isChecked(),
            "clock_format":      self._clock_format.currentText(),
            "show_lang":         self._show_lang.isChecked(),
            "show_theme_toggle": self._show_theme_toggle.isChecked(),
        }

    def set_values(self, d: dict):
        if "show_header"       in d: self._show_header.setChecked(d["show_header"])
        if "header_height"     in d: self._header_height.setValue(d["header_height"])
        if "header_bg"         in d: self._header_bg.set_color(d["header_bg"])
        if "header_text_color" in d: self._header_text_color.set_color(d["header_text_color"])
        if "show_title"        in d: self._show_title.setChecked(d["show_title"])
        if "title_text"        in d: self._title_text.setText(d["title_text"])
        if "title_font_size"   in d: self._title_font_size.setValue(d["title_font_size"])
        if "title_position"    in d: self._title_position.setCurrentText(d["title_position"])
        if "show_logo"         in d: self._show_logo.setChecked(d["show_logo"])
        if "logo_url"          in d: self._logo_url.setText(d["logo_url"])
        if "logo_position"     in d: self._logo_position.setCurrentText(d["logo_position"])
        if "logo_height"       in d: self._logo_height.setValue(d["logo_height"])
        if "logo_clickable"    in d: self._logo_clickable.setChecked(d["logo_clickable"])
        if "show_clock"        in d: self._show_clock.setChecked(d["show_clock"])
        if "clock_format"      in d: self._clock_format.setCurrentText(d["clock_format"])
        if "show_lang"         in d: self._show_lang.setChecked(d["show_lang"])
        if "show_theme_toggle" in d: self._show_theme_toggle.setChecked(d["show_theme_toggle"])
