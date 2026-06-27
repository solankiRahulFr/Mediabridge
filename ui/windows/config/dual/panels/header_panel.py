"""
Header Panel  –  show/hide, logo URL, title text, position, branding colours.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QLineEdit,
    QSpinBox, QWidget,
)
from core.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from .base_panel import BasePanel
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
            title_key="config_dual_mode.header.visibility",
            desc_key="config_dual_mode.header.visibility.desc",
        )
        self.setStyleSheet("background-color: transparent;")

        self._show_header = QCheckBox("")
        self._bind_text(self._show_header, "config_dual_mode.header.show_header_text")
        self._show_header.setChecked(True)
        sec.addLayout(self._row("Header Visible", self._show_header,
                               label_key="config_dual_mode.header.show_header_label"))

        self._header_height = QSpinBox()
        self._header_height.setRange(40, 200)
        self._header_height.setValue(64)
        self._header_height.setSuffix("  px")
        sec.addLayout(self._row("Header Height", self._header_height,
                               label_key="config_dual_mode.header.height"))

        self._header_bg = ColorPicker("#13161E")
        sec.addLayout(self._row("Header Background", self._header_bg,
                               label_key="config_dual_mode.header.bg"))

        self._header_text_color = ColorPicker("#EEF0F8")
        sec.addLayout(self._row("Header Text Color", self._header_text_color,
                               label_key="config_dual_mode.header.text_color"))

        # ── Title ─────────────────────────────────────────────────────────────
        tsec = self._section("Title",
                            title_key="config_dual_mode.header.title_section")

        self._show_title = QCheckBox("")
        self._bind_text(self._show_title, "config_dual_mode.header.show_title_text")
        self._show_title.setChecked(True)
        tsec.addLayout(self._row("Show Title", self._show_title,
                                label_key="config_dual_mode.header.show_title_label"))

        self._title_text = QLineEdit()
        self._bind_placeholder(self._title_text, "config_dual_mode.header.title_text_placeholder")
        tsec.addLayout(self._row("Title Text", self._title_text,
                                label_key="config_dual_mode.header.title_text"))

        self._title_font_size = QSpinBox()
        self._title_font_size.setRange(10, 72)
        self._title_font_size.setValue(18)
        self._title_font_size.setSuffix("  pt")
        tsec.addLayout(self._row("Title Font Size", self._title_font_size,
                                label_key="config_dual_mode.header.title_font_size"))

        self._title_position = QComboBox()
        for p in ["Left", "Centre", "Right"]:
            self._title_position.addItem(p)
        self._bind_combobox_items(self._title_position, [
            "config_dual_mode.header.title_position.option_left",
            "config_dual_mode.header.title_position.option_center",
            "config_dual_mode.header.title_position.option_right",
        ])
        tsec.addLayout(self._row("Title Position", self._title_position,
                                label_key="config_dual_mode.header.title_position"))

        # ── Logo ──────────────────────────────────────────────────────────────
        lsec = self._section(
            "Logo",
            "Supports local file paths and remote URLs. "
            "SVG is recommended for crisp 4K rendering.",
            title_key="config_dual_mode.header.logo",
            desc_key="config_dual_mode.header.logo.desc",
        )

        self._show_logo = QCheckBox("")
        self._bind_text(self._show_logo, "config_dual_mode.header.show_logo_text")
        self._show_logo.setChecked(True)
        lsec.addLayout(self._row("Show Logo", self._show_logo,
                                label_key="config_dual_mode.header.show_logo_label"))

        self._logo_url = QLineEdit()
        self._bind_placeholder(self._logo_url, "config_dual_mode.header.logo_url_placeholder")
        lsec.addLayout(self._row("Logo URL / Path", self._logo_url,
                                label_key="config_dual_mode.header.logo_url"))

        self._logo_position = QComboBox()
        for p in ["Left", "Right", "Centre"]:
            self._logo_position.addItem(p)
        self._bind_combobox_items(self._logo_position, [
            "config_dual_mode.header.logo_position.option_left",
            "config_dual_mode.header.logo_position.option_right",
            "config_dual_mode.header.logo_position.option_center",
        ])
        lsec.addLayout(self._row("Logo Position", self._logo_position,
                                label_key="config_dual_mode.header.logo_position"))

        self._logo_height = QSpinBox()
        self._logo_height.setRange(16, 160)
        self._logo_height.setValue(40)
        self._logo_height.setSuffix("  px")
        lsec.addLayout(self._row("Logo Max Height", self._logo_height,
                                label_key="config_dual_mode.header.logo_height"))

        self._logo_clickable = QCheckBox("")
        self._bind_text(self._logo_clickable, "config_dual_mode.header.logo_clickable_text")
        lsec.addLayout(self._row("Logo as Exit Target", self._logo_clickable,
                                 "Users must tap the logo N times to unlock kiosk mode",
                                 label_key="config_dual_mode.header.logo_clickable_label",
                                 hint_key="config_dual_mode.header.logo_clickable.hint"))

        # ── Extras ────────────────────────────────────────────────────────────
        xsec = self._section("Header Extras",
                            title_key="config_dual_mode.header.extras")

        self._show_clock = QCheckBox("")
        self._bind_text(self._show_clock, "config_dual_mode.header.show_clock_text")
        xsec.addLayout(self._row("Clock", self._show_clock,
                                label_key="config_dual_mode.header.show_clock_label"))

        self._clock_format = QComboBox()
        for f in ["HH:MM", "HH:MM:SS", "HH:MM  (12h AM/PM)", "Day, DD MMM YYYY  HH:MM"]:
            self._clock_format.addItem(f)
        self._bind_combobox_items(self._clock_format, [
            "config_dual_mode.header.clock_format.option_hm",
            "config_dual_mode.header.clock_format.option_hms",
            "config_dual_mode.header.clock_format.option_hm12",
            "config_dual_mode.header.clock_format.option_full",
        ])
        xsec.addLayout(self._row("Clock Format", self._clock_format,
                                label_key="config_dual_mode.header.clock_format"))

        self._show_lang = QCheckBox("")
        self._bind_text(self._show_lang, "config_dual_mode.header.show_lang_text")
        self._show_lang.setChecked(True)
        xsec.addLayout(self._row("Language Switcher", self._show_lang,
                                label_key="config_dual_mode.header.show_lang_label"))

        self._show_theme_toggle = QCheckBox("")
        self._bind_text(self._show_theme_toggle, "config_dual_mode.header.show_theme_toggle_text")
        xsec.addLayout(self._row("Theme Toggle", self._show_theme_toggle,
                                label_key="config_dual_mode.header.show_theme_toggle_label"))

        self._root.addStretch()
        
        # Apply initial translations
        self.retranslate_ui()

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

    def retranslate_ui(self) -> None:
        """Update translatable strings."""
        super().retranslate_ui()  # Call parent to update all bound labels