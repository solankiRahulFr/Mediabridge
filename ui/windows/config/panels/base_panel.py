"""
ui/windows/config/base_panel.py
─────────────────────────────────────────────────────────────────────────────
BasePanel — shared layout helpers for all config panels.

Every panel inherits from this.  It provides:
  • _section(title, desc?)  → QVBoxLayout inside a styled Card frame
  • _row(label, widget, hint?)  → labelled field row layout
  • _divider()  → QFrame horizontal rule
  • Abstract get_values() / set_values() contract
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager


class BasePanel(QWidget):
    """Base class for all ConfigWindow panels."""

    LABEL_WIDTH = 210   # px — consistent left-column width across all panels

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(20)

    # ── Layout helpers ────────────────────────────────────────────────────────

    def _section(self, title: str, desc: str = "") -> QVBoxLayout:
        """
        Create a Card-styled frame with a section title (and optional
        description), append it to the panel's root layout, and return
        the card's inner QVBoxLayout so the caller can add rows into it.
        """
        card = QFrame()
        card.setObjectName("Card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 16, 20, 20)
        inner.setSpacing(14)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("SectionTitle")
        inner.addWidget(title_lbl)

        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("SectionDesc")
            desc_lbl.setWordWrap(True)
            inner.addWidget(desc_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        inner.addWidget(line)

        self._root.addWidget(card)
        return inner

    def _row(self, label: str, widget: QWidget,
             hint: str = "") -> QVBoxLayout:
        """
        Return a QVBoxLayout containing:
          [FieldLabel  |  widget]
          [optional hint text    ]

        Callers do:
            sec.addLayout(self._row("Fullscreen", self._fullscreen_cb))
        """
        outer = QVBoxLayout()
        outer.setSpacing(3)

        row = QHBoxLayout()

        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(self.LABEL_WIDTH)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        row.addWidget(lbl)
        row.addWidget(widget, 1)

        outer.addLayout(row)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("HintLabel")
            hint_lbl.setWordWrap(True)
            hint_lbl.setContentsMargins(self.LABEL_WIDTH + 4, 0, 0, 0)
            outer.addWidget(hint_lbl)

        return outer

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setFrameShape(QFrame.HLine)
        return d

    # ── Contract ──────────────────────────────────────────────────────────────

    def get_values(self) -> dict:
        """Return all panel settings as a JSON-serialisable dict."""
        raise NotImplementedError

    def set_values(self, d: dict) -> None:
        """Restore panel state from a previously saved dict."""
        raise NotImplementedError