"""
ui/widgets/color_picker.py
─────────────────────────────────────────────────────────────────────────────
Compact colour swatch + hex label that opens QColorDialog on click.
Reused by display_panel and header_panel — lives in widgets/ so it's
available to any future panel or window without circular imports.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QPushButton, QWidget


class ColorPicker(QWidget):
    """
    A 32×32 colour swatch button + hex label.
    Emits color_changed(hex_str) when the user picks a new colour.

    Usage:
        picker = ColorPicker("#4F8EF7")
        picker.color_changed.connect(lambda h: print(h))
        hex_val = picker.color_hex()
    """

    color_changed = Signal(str)   # emits hex string, e.g. "#4F8EF7"

    def __init__(self, default_hex: str = "#0D0F14",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = QColor(default_hex)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._btn = QPushButton()
        self._btn.setFixedSize(32, 32)
        self._btn.setObjectName("SmallBtn")
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._open_dialog)
        lay.addWidget(self._btn)

        self._label = QLabel(default_hex)
        self._label.setObjectName("FieldLabel")
        lay.addWidget(self._label)
        lay.addStretch()

        self._refresh()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _open_dialog(self) -> None:
        chosen = QColorDialog.getColor(self._color, self, "Pick Colour")
        if chosen.isValid():
            self._color = chosen
            self._label.setText(chosen.name())
            self._refresh()
            self.color_changed.emit(chosen.name())

    def _refresh(self) -> None:
        self._btn.setStyleSheet(
            f"background-color:{self._color.name()};"
            "border-radius:6px; border:1px solid #555;"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def color_hex(self) -> str:
        """Return the currently selected colour as a lowercase hex string."""
        return self._color.name()

    def set_color(self, hex_str: str) -> None:
        """Programmatically set the colour without opening the dialog."""
        c = QColor(hex_str)
        if c.isValid():
            self._color = c
            self._label.setText(hex_str)
            self._refresh()