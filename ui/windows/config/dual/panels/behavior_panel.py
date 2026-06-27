"""
Behavior Panel  –  autostart, kiosk lock, idle/screensaver, exit gesture.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QSpinBox, QLineEdit,QWidget,
)

from core.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from .base_panel import BasePanel


class BehaviorPanel(BasePanel):
    def __init__(self, tm: ThemeManager, parent: QWidget | None = None):
        super().__init__(tm, parent)
        self._build()

    def _build(self):
        # ── Startup ───────────────────────────────────────────────────────────
        sec = self._section(
            "Startup",
            "Control how the kiosk application launches on boot.",
            title_key="config_dual_mode.behavior.startup",
            desc_key="config_dual_mode.behavior.startup.desc",
        )
        self.setStyleSheet("background-color: transparent;")

        self._autostart = QCheckBox("")
        self._bind_text(self._autostart, "config_dual_mode.behavior.autostart_checkbox")
        sec.addLayout(self._row("Auto-start", self._autostart,
                               label_key="config_dual_mode.behavior.autostart_label"))

        self._startup_delay = QSpinBox()
        self._startup_delay.setRange(0, 120)
        self._startup_delay.setSuffix("  sec")
        self._startup_delay.setValue(3)
        sec.addLayout(self._row("Startup Delay", self._startup_delay,
                                "Wait N seconds after boot before launching",
                                label_key="config_dual_mode.behavior.startup_delay",
                                hint_key="config_dual_mode.behavior.startup_delay.hint"))

        self._start_page = QComboBox()
        for p in ["Home / Landing", "Last visited page", "Specific content ID"]:
            self._start_page.addItem(p)
        self._bind_combobox_items(self._start_page, [
            "config_dual_mode.behavior.start_page.option_home",
            "config_dual_mode.behavior.start_page.option_last",
            "config_dual_mode.behavior.start_page.option_specific",
        ])
        sec.addLayout(self._row("Start Page", self._start_page,
                               label_key="config_dual_mode.behavior.start_page")) 

        self._start_id = QLineEdit()
        self._bind_placeholder(self._start_id, "config_dual_mode.behavior.start_content_id_placeholder")
        sec.addLayout(self._row("Start Content ID", self._start_id,
                                'Only used when "Specific content ID" is selected above',
                                label_key="config_dual_mode.behavior.start_content_id"))

        # ── Kiosk Lock ────────────────────────────────────────────────────────
        ksec = self._section(
            "Kiosk Mode Lock",
            "Prevent users from accessing the OS or closing the application accidentally.",
            title_key="config_dual_mode.behavior.kiosk_lock",
            desc_key="config_dual_mode.behavior.kiosk_lock.desc",
        )

        self._kiosk_mode = QCheckBox("")
        self._bind_text(self._kiosk_mode, "config_dual_mode.behavior.kiosk_mode_checkbox")
        self._kiosk_mode.setChecked(True)
        ksec.addLayout(self._row("Kiosk Lock", self._kiosk_mode,
                                label_key="config_dual_mode.behavior.kiosk_mode_label"))

        self._disable_rightclick = QCheckBox("")
        self._bind_text(self._disable_rightclick, "config_dual_mode.behavior.disable_rightclick_checkbox")
        self._disable_rightclick.setChecked(True)
        ksec.addLayout(self._row("Right-click", self._disable_rightclick,
                                label_key="config_dual_mode.behavior.disable_rightclick_label"))

        self._disable_keyboard = QCheckBox("")
        self._bind_text(self._disable_keyboard, "config_dual_mode.behavior.disable_keyboard_checkbox")
        ksec.addLayout(self._row("OS Shortcuts", self._disable_keyboard,
                                label_key="config_dual_mode.behavior.disable_keyboard_label"))

        # ── Exit Gesture ──────────────────────────────────────────────────────
        esec = self._section(
            "Exit / Unlock Gesture",
            (
                "Choose how a technician can force-exit kiosk mode without a physical keyboard. "
                "Recommendation: use a corner multi-tap — invisible to end users, hard to trigger accidentally."
            ),
            title_key="config_dual_mode.behavior.exit_gesture",
            desc_key="config_dual_mode.behavior.exit_gesture.desc",
        )

        self._exit_method = QComboBox()
        for m in [
            "Corner tap  (N taps on any corner)",
            "Logo multi-tap  (N taps on header logo)",
            "Hidden button  (invisible overlay in corner)",
            "PIN code dialog",
            "Keyboard shortcut only  (no gesture)",
        ]:
            self._exit_method.addItem(m)
        self._bind_combobox_items(self._exit_method, [
            "config_dual_mode.behavior.exit_method.option_corner",
            "config_dual_mode.behavior.exit_method.option_logo",
            "config_dual_mode.behavior.exit_method.option_button",
            "config_dual_mode.behavior.exit_method.option_pin",
            "config_dual_mode.behavior.exit_method.option_keyboard",
        ])
        esec.addLayout(self._row("Exit Method", self._exit_method,
                                label_key="config_dual_mode.behavior.exit_method"))

        self._exit_taps = QSpinBox()
        self._exit_taps.setRange(3, 20)
        self._exit_taps.setValue(7)
        esec.addLayout(self._row("Required Taps / Clicks", self._exit_taps,
                                 "5 = easy  ·  7 = balanced  ·  10 = hard to trigger accidentally",
                                 label_key="config_dual_mode.behavior.exit_taps",
                                 hint_key="config_dual_mode.behavior.exit_taps.hint"))

        self._exit_timeout = QSpinBox()
        self._exit_timeout.setRange(1, 30)
        self._exit_timeout.setValue(5)
        self._exit_timeout.setSuffix("  sec")
        esec.addLayout(self._row("Tap Window", self._exit_timeout,
                                 label_key="config_dual_mode.behavior.exit_timeout",
                                 hint_key="config_dual_mode.behavior.exit_timeout.hint"))

        self._exit_corner = QComboBox()
        for c in ["Top-left", "Top-right", "Bottom-left", "Bottom-right"]:
            self._exit_corner.addItem(c)
        self._bind_combobox_items(self._exit_corner, [
            "config_dual_mode.behavior.exit_corner.option_tl",
            "config_dual_mode.behavior.exit_corner.option_tr",
            "config_dual_mode.behavior.exit_corner.option_bl",
            "config_dual_mode.behavior.exit_corner.option_br",
        ])
        self._exit_corner.setCurrentText("Bottom-right")
        esec.addLayout(self._row("Corner (for corner tap)", self._exit_corner))

        self._exit_pin = QLineEdit()
        self._bind_placeholder(self._exit_pin, "config_dual_mode.behavior.exit_pin_placeholder")
        self._exit_pin.setEchoMode(QLineEdit.Password)
        esec.addLayout(self._row("Exit PIN", self._exit_pin))

        # ── Idle / Screensaver ────────────────────────────────────────────────
        isec = self._section("Idle & Screensaver")

        self._idle_timeout = QSpinBox()
        self._idle_timeout.setRange(0, 3600)
        self._idle_timeout.setSuffix("  sec  (0 = disabled)")
        self._idle_timeout.setValue(120)
        isec.addLayout(self._row("Idle Timeout", self._idle_timeout,
                                 label_key="config_dual_mode.behavior.idle_timeout",
                                 hint_key="config_dual_mode.behavior.idle_timeout.hint"))

        self._idle_action = QComboBox()
        for a in ["Return to home page", "Show screensaver / attract loop",
                  "Dim screen", "Blank screen"]:
            self._idle_action.addItem(a)
        self._bind_combobox_items(self._idle_action, [
            "config_dual_mode.behavior.idle_action.option_home",
            "config_dual_mode.behavior.idle_action.option_attract",
            "config_dual_mode.behavior.idle_action.option_dim",
            "config_dual_mode.behavior.idle_action.option_blank",
        ])
        isec.addLayout(self._row("Idle Action", self._idle_action))

        self._attract_path = QLineEdit()
        self._bind_placeholder(self._attract_path, "config_dual_mode.behavior.attract_path_placeholder")
        isec.addLayout(self._row("Attract Loop Media", self._attract_path,
                                 label_key="config_dual_mode.behavior.attract_path",
                                 hint_key="config_dual_mode.behavior.attract_path.hint"))

        self._root.addStretch()
        
        # Apply initial translations
        self.retranslate_ui()

    # ── serialisation ─────────────────────────────────────────────────────────
    def get_values(self) -> dict:
        return {
            "autostart":          self._autostart.isChecked(),
            "startup_delay":      self._startup_delay.value(),
            "start_page":         self._start_page.currentText(),
            "start_content_id":   self._start_id.text().strip(),
            "kiosk_mode":         self._kiosk_mode.isChecked(),
            "disable_rightclick": self._disable_rightclick.isChecked(),
            "disable_keyboard":   self._disable_keyboard.isChecked(),
            "exit_method":        self._exit_method.currentText(),
            "exit_taps":          self._exit_taps.value(),
            "exit_timeout_sec":   self._exit_timeout.value(),
            "exit_corner":        self._exit_corner.currentText(),
            "exit_pin":           self._exit_pin.text(),
            "idle_timeout_sec":   self._idle_timeout.value(),
            "idle_action":        self._idle_action.currentText(),
            "attract_loop_path":  self._attract_path.text().strip(),
        }

    def set_values(self, d: dict):
        if "autostart"          in d: self._autostart.setChecked(d["autostart"])
        if "startup_delay"      in d: self._startup_delay.setValue(d["startup_delay"])
        if "start_page"         in d: self._start_page.setCurrentText(d["start_page"])
        if "start_content_id"   in d: self._start_id.setText(d["start_content_id"])
        if "kiosk_mode"         in d: self._kiosk_mode.setChecked(d["kiosk_mode"])
        if "disable_rightclick" in d: self._disable_rightclick.setChecked(d["disable_rightclick"])
        if "disable_keyboard"   in d: self._disable_keyboard.setChecked(d["disable_keyboard"])
        if "exit_method"        in d: self._exit_method.setCurrentText(d["exit_method"])
        if "exit_taps"          in d: self._exit_taps.setValue(d["exit_taps"])
        if "exit_timeout_sec"   in d: self._exit_timeout.setValue(d["exit_timeout_sec"])
        if "exit_corner"        in d: self._exit_corner.setCurrentText(d["exit_corner"])
        if "exit_pin"           in d: self._exit_pin.setText(d["exit_pin"])
        if "idle_timeout_sec"   in d: self._idle_timeout.setValue(d["idle_timeout_sec"])
        if "idle_action"        in d: self._idle_action.setCurrentText(d["idle_action"])
        if "attract_loop_path"  in d: self._attract_path.setText(d["attract_loop_path"])

    def retranslate_ui(self) -> None:
        """Update translatable strings."""
        super().retranslate_ui()  # Call parent to update all bound labels