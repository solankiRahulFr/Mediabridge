"""
BasePanel — abstract base class for all configuration panels.

Provides:
    • ``_section(title, desc)``  — creates a titled card with a QVBoxLayout
    • ``_row(label, widget, hint)`` — creates a label + widget + optional hint row
    • ``_root``                   — the panel's main QVBoxLayout

Every config panel (DisplayPanel, BehaviorPanel, HeaderPanel, MappingPanel)
inherits from BasePanel so that the visual structure is consistent without
duplicating layout boilerplate.

Usage
─────
    from core.base_panel import BasePanel
    from core.theme import ThemeManager

    class MyPanel(BasePanel):
        def __init__(self, tm: ThemeManager, parent=None):
            super().__init__(tm, parent)
            sec = self._section("Section Title", "Optional description")
            sec.addLayout(self._row("Label", some_widget, "Hint text")[0])
            self._root.addStretch()
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy,
    QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt


class BasePanel(QWidget):
    """
    Base class for config-panel widgets.

    Parameters
    ----------
    tm : ThemeManager
        The shared ThemeManager instance (used for colour lookups if needed).
    parent : QWidget | None
        Optional parent widget.
    """

    def __init__(self, tm, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(20)

    # ── Section card ──────────────────────────────────────────────────────────

    def _section(self, title: str, desc: str = "") -> QVBoxLayout:
        """
        Create a titled card frame and return its inner QVBoxLayout.

        The frame gets ``objectName="Card"`` so the global QSS styles it
        automatically.
        """
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 18, 20, 18)
        inner.setSpacing(12)

        lbl = QLabel(title)
        lbl.setObjectName("SectionTitle")
        inner.addWidget(lbl)

        if desc:
            d = QLabel(desc)
            d.setObjectName("SectionDesc")
            d.setWordWrap(True)
            inner.addWidget(d)

        self._root.addWidget(card)
        return inner

    # ── Row helper ────────────────────────────────────────────────────────────

    def _row(
        self,
        label: str,
        widget: QWidget,
        hint: str = "",
    ) -> tuple[QVBoxLayout, QWidget]:
        """
        Build a label + widget row with an optional hint underneath.

        Returns ``(outer_layout, widget)`` so callers can add additional items.
        """
        outer = QVBoxLayout()
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(12)

        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(180)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(lbl)

        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row.addWidget(widget)

        outer.addLayout(row)

        if hint:
            h = QLabel(hint)
            h.setObjectName("HintLabel")
            h.setContentsMargins(192, 0, 0, 0)
            h.setWordWrap(True)
            outer.addWidget(h)

        return outer, widget
