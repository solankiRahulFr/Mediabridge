"""
ui/windows/config/base_panel.py
─────────────────────────────────────────────────────────────────────────────
BasePanel — shared layout helpers for all config panels.

Every panel inherits from this.  It provides:
  • _section(title, desc?, title_key?, desc_key?)  → QVBoxLayout inside a styled Card frame
  • _row(label, widget, hint?, label_key?, hint_key?)  → labelled field row layout
  • _divider()  → QFrame horizontal rule
  • Abstract get_values() / set_values() contract
  • I18nMixin capabilities for automatic language switching
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from core.app_state import get_state


class BasePanel(I18nMixin, QWidget):
    """Base class for all ConfigWindow panels."""

    LABEL_WIDTH = 210   # px — consistent left-column width across all panels

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._state = get_state()
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self._root.setSpacing(20)
        
        # Track labels bound to i18n keys for retranslation
        self._section_titles = []  # List of (label_widget, i18n_key) tuples
        self._section_descs = []   # List of (label_widget, i18n_key) tuples
        self._row_labels = []      # List of (label_widget, i18n_key) tuples
        self._row_hints = []       # List of (label_widget, i18n_key) tuples
        self._combobox_bindings = {}  # Dict of combobox_id -> (combobox, item_keys)

    # ── Layout helpers ────────────────────────────────────────────────────────

    def _section(self, title: str, desc: str = "", 
                 title_key: str = "", desc_key: str = "") -> QVBoxLayout:
        """
        Create a Card-styled frame with a section title (and optional
        description), append it to the panel's root layout, and return
        the card's inner QVBoxLayout so the caller can add rows into it.
        
        Args:
            title: Display text (used if title_key not provided)
            desc: Description text (used if desc_key not provided)
            title_key: i18n key for title translation
            desc_key: i18n key for description translation
        """
        card = QFrame()
        card.setObjectName("Card")
        inner = QVBoxLayout(card)
        inner.setContentsMargins(20, 16, 20, 20)
        inner.setSpacing(14)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("SectionTitle")
        if title_key:
            # Bind to translation key
            actual_text = self._state.lang.t(title_key)
            title_lbl.setText(actual_text)
            self._section_titles.append((title_lbl, title_key))
        inner.addWidget(title_lbl)

        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("SectionDesc")
            desc_lbl.setWordWrap(True)
            if desc_key:
                # Bind to translation key
                actual_text = self._state.lang.t(desc_key)
                desc_lbl.setText(actual_text)
                self._section_descs.append((desc_lbl, desc_key))
            inner.addWidget(desc_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        inner.addWidget(line)

        self._root.addWidget(card)
        return inner

    def _row(self, label: str, widget: QWidget,
             hint: str = "", label_key: str = "", hint_key: str = "") -> QVBoxLayout:
        """
        Return a QVBoxLayout containing:
          [FieldLabel  |  widget]
          [optional hint text    ]

        Args:
            label: Display text (used if label_key not provided)
            widget: The widget for this row
            hint: Hint text (used if hint_key not provided)
            label_key: i18n key for label translation
            hint_key: i18n key for hint translation
        
        Callers do:
            sec.addLayout(self._row("Fullscreen", self._fullscreen_cb, 
                                   label_key="config_dual_mode.display.fullscreen"))
        """
        outer = QVBoxLayout()
        outer.setSpacing(3)

        row = QHBoxLayout()

        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(self.LABEL_WIDTH)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        if label_key:
            # Bind to translation key
            actual_text = self._state.lang.t(label_key)
            lbl.setText(actual_text)
            self._row_labels.append((lbl, label_key))
        row.addWidget(lbl)
        row.addWidget(widget, 1)

        outer.addLayout(row)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("HintLabel")
            hint_lbl.setWordWrap(True)
            hint_lbl.setContentsMargins(self.LABEL_WIDTH + 4, 0, 0, 0)
            if hint_key:
                # Bind to translation key
                actual_text = self._state.lang.t(hint_key)
                hint_lbl.setText(actual_text)
                self._row_hints.append((hint_lbl, hint_key))
            outer.addWidget(hint_lbl)

        return outer

    @staticmethod
    def _divider() -> QFrame:
        d = QFrame()
        d.setFrameShape(QFrame.HLine)
        return d

    # ── i18n support ───────────────────────────────────────────────────────────

    def _bind_combobox_items(self, combobox, item_keys: list[str]) -> None:
        """
        Bind combobox items to translation keys for dynamic language switching.
        
        Args:
            combobox: The QComboBox to bind
            item_keys: List of i18n keys for each item (order must match combobox items)
        
        Example:
            self._orientation = QComboBox()
            self._orientation.addItem("Landscape")
            self._orientation.addItem("Portrait")
            self._bind_combobox_items(self._orientation, 
                                     ["orientation.landscape", "orientation.portrait"])
        """
        self._combobox_bindings[id(combobox)] = (combobox, item_keys)

    def retranslate_ui(self) -> None:
        """Update all i18n-bound labels and combobox items when language changes."""
        # Update section titles
        for lbl, key in self._section_titles:
            lbl.setText(self._state.lang.t(key))
        
        # Update section descriptions
        for lbl, key in self._section_descs:
            lbl.setText(self._state.lang.t(key))
        
        # Update row labels
        for lbl, key in self._row_labels:
            lbl.setText(self._state.lang.t(key))
        
        # Update row hints
        for lbl, key in self._row_hints:
            lbl.setText(self._state.lang.t(key))
        
        # Update combobox items
        for combobox, item_keys in self._combobox_bindings.values():
            for i, key in enumerate(item_keys):
                combobox.setItemText(i, self._state.lang.t(key))
        
        I18nMixin._do_retranslate(self)

    # ── Contract ──────────────────────────────────────────────────────────────

    def get_values(self) -> dict:
        """Return all panel settings as a JSON-serialisable dict."""
        raise NotImplementedError

    def set_values(self, d: dict) -> None:
        """Restore panel state from a previously saved dict."""
        raise NotImplementedError
