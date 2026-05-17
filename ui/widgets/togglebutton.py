"""
Compact animated theme toggle for the launcher header bar.

This is visually distinct from the config-window's ThemeToggle
(``ui/themes/theme.py``):  smaller (56×28), different icon set (☽ / ☀),
shadow on knob.  Both read colour tokens from the central ThemeManager.
"""

from PySide6.QtCore import (
    Property as QtProperty, QEasingCurve,
    QPropertyAnimation, QRect, Qt, Signal,
)
from PySide6.QtGui import QColor, QCursor, QFont, QPainter
from PySide6.QtWidgets import QWidget

from core.app_state import get_state
from ui.themes.theme import THEMES


class ThemeToggle(QWidget):
    toggled = Signal(bool)  # True = dark

    def __init__(self, is_dark=True, parent=None):
        super().__init__(parent)
        self._dark = is_dark
        self.__knob_x = 32.0 if is_dark else 4.0
        self.setFixedSize(56, 28)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    # ── Qt property for animation ─────────────────────────────────────────────
    def get_knob_x(self):
        return self.__knob_x

    def set_knob_x(self, v):
        self.__knob_x = v
        self.update()

    knob_x = QtProperty(float, get_knob_x, set_knob_x)

    def animate_to(self, target):
        self._anim = QPropertyAnimation(self, b"knob_x", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.setStartValue(self.__knob_x)
        self._anim.setEndValue(target)
        self._anim.start()

    def mousePressEvent(self, _):
        self._dark = not self._dark
        self.animate_to(32.0 if self._dark else 4.0)
        self.toggled.emit(self._dark)

    def _get_colors(self) -> dict[str, str]:
        state = get_state()
        if state.theme:
            return state.theme.colors
        return THEMES["dark" if self._dark else "light"]

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self._get_colors()

        p.setBrush(QColor(t["accent"]) if self._dark else QColor(t["border"]))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 56, 28, 14, 14)

        font = QFont()
        font.setPointSize(8)
        p.setFont(font)
        p.setPen(QColor("#FFFFFF" if self._dark else t["text2"]))
        p.drawText(QRect(5, 0, 18, 28), Qt.AlignCenter, "☽")
        p.setPen(QColor(t["text2"]))
        p.drawText(QRect(33, 0, 18, 28), Qt.AlignCenter, "☀")

        # knob shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawEllipse(int(self.__knob_x) + 1, 5, 20, 20)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(int(self.__knob_x), 4, 20, 20)
