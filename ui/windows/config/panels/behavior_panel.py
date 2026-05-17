"""
Behavior Panel  –  autostart, kiosk lock, idle/screensaver, exit gesture.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QSpinBox, QLineEdit,QWidget,
)

from core.base_panel import BasePanel
from core.theme import ThemeManager


class BehaviorPanel(BasePanel):
    def __init__(self, tm: ThemeManager, parent: QWidget | None = None):
        super().__init__(tm, parent)
        self._build()

    def _build(self):
        # ── Startup ───────────────────────────────────────────────────────────
        sec = self._section(
            "Startup",
            "Control how the kiosk application launches on boot.",
        )

        self._autostart = QCheckBox("Auto-start on system boot")
        sec.addLayout(self._row("Auto-start", self._autostart)[0])

        self._startup_delay = QSpinBox()
        self._startup_delay.setRange(0, 120)
        self._startup_delay.setSuffix("  sec")
        self._startup_delay.setValue(3)
        sec.addLayout(self._row("Startup Delay", self._startup_delay,
                                "Wait N seconds after boot before launching")[0])

        self._start_page = QComboBox()
        for p in ["Home / Landing", "Last visited page", "Specific content ID"]:
            self._start_page.addItem(p)
        sec.addLayout(self._row("Start Page", self._start_page)[0])

        self._start_id = QLineEdit()
        self._start_id.setPlaceholderText("e.g. content-slug or UUID")
        sec.addLayout(self._row("Start Content ID", self._start_id,
                                'Only used when "Specific content ID" is selected above')[0])

        # ── Kiosk Lock ────────────────────────────────────────────────────────
        ksec = self._section(
            "Kiosk Mode Lock",
            "Prevent users from accessing the OS or closing the application accidentally.",
        )

        self._kiosk_mode = QCheckBox("Enable kiosk lock  (blocks Alt-F4, task-switcher, etc.)")
        self._kiosk_mode.setChecked(True)
        ksec.addLayout(self._row("Kiosk Lock", self._kiosk_mode)[0])

        self._disable_rightclick = QCheckBox("Disable right-click context menus")
        self._disable_rightclick.setChecked(True)
        ksec.addLayout(self._row("Right-click", self._disable_rightclick)[0])

        self._disable_keyboard = QCheckBox("Block OS keyboard shortcuts (Win key, Alt-Tab…)")
        ksec.addLayout(self._row("OS Shortcuts", self._disable_keyboard)[0])

        # ── Exit Gesture ──────────────────────────────────────────────────────
        esec = self._section(
            "Exit / Unlock Gesture",
            (
                "Choose how a technician can force-exit kiosk mode without a physical keyboard. "
                "Recommendation: use a corner multi-tap — invisible to end users, hard to trigger accidentally."
            ),
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
        esec.addLayout(self._row("Exit Method", self._exit_method)[0])

        self._exit_taps = QSpinBox()
        self._exit_taps.setRange(3, 20)
        self._exit_taps.setValue(7)
        esec.addLayout(self._row("Required Taps / Clicks", self._exit_taps,
                                 "5 = easy  ·  7 = balanced  ·  10 = hard to trigger accidentally")[0])

        self._exit_timeout = QSpinBox()
        self._exit_timeout.setRange(1, 30)
        self._exit_timeout.setValue(5)
        self._exit_timeout.setSuffix("  sec")
        esec.addLayout(self._row("Tap Window", self._exit_timeout,
                                 "All taps must occur within this time window")[0])

        self._exit_corner = QComboBox()
        for c in ["Top-left", "Top-right", "Bottom-left", "Bottom-right"]:
            self._exit_corner.addItem(c)
        self._exit_corner.setCurrentText("Bottom-right")
        esec.addLayout(self._row("Corner (for corner tap)", self._exit_corner)[0])

        self._exit_pin = QLineEdit()
        self._exit_pin.setPlaceholderText("4-8 digit PIN  (only used when PIN mode is active)")
        self._exit_pin.setEchoMode(QLineEdit.Password)
        esec.addLayout(self._row("Exit PIN", self._exit_pin)[0])

        # ── Idle / Screensaver ────────────────────────────────────────────────
        isec = self._section("Idle & Screensaver")

        self._idle_timeout = QSpinBox()
        self._idle_timeout.setRange(0, 3600)
        self._idle_timeout.setSuffix("  sec  (0 = disabled)")
        self._idle_timeout.setValue(120)
        isec.addLayout(self._row("Idle Timeout", self._idle_timeout,
                                 "Return to home after N seconds of inactivity")[0])

        self._idle_action = QComboBox()
        for a in ["Return to home page", "Show screensaver / attract loop",
                  "Dim screen", "Blank screen"]:
            self._idle_action.addItem(a)
        isec.addLayout(self._row("Idle Action", self._idle_action)[0])

        self._attract_path = QLineEdit()
        self._attract_path.setPlaceholderText("/path/to/attract_loop.mp4  or  URL")
        isec.addLayout(self._row("Attract Loop Media", self._attract_path,
                                 'Used when Idle Action is "Show screensaver / attract loop"')[0])

        self._root.addStretch()

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
