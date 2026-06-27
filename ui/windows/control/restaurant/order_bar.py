from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QWidget,
)

from ui.themes.theme import ThemeManager

logger = logging.getLogger(__name__)


class OrderBar(QWidget):
    submit_order = Signal(list)  # emits the full order list

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self.setFixedHeight(64)
        self._build()

    def _build(self) -> None:
        t = self._tm.colors
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(16)

        # Item count
        self._count_lbl = QLabel("0 items")
        self._count_lbl.setStyleSheet(
            f"font-size: 13px; color: {t['text2']}; background: transparent;"
        )
        lay.addWidget(self._count_lbl)

        # Total price
        self._total_lbl = QLabel("€0.00")
        total_font = QFont()
        total_font.setPointSize(14)
        total_font.setWeight(QFont.Bold)
        self._total_lbl.setFont(total_font)
        self._total_lbl.setStyleSheet(
            f"color: {t['accent']}; background: transparent;"
        )
        lay.addWidget(self._total_lbl)

        lay.addStretch()

        # Clear button
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("SecondaryBtn")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setFixedHeight(38)
        self._clear_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {t['danger']}; "
            f"border: 1px solid {t['danger']}; border-radius: 8px; "
            f"padding: 0 16px; font-size: 12px; }}"
            f"QPushButton:hover {{ background: {t['danger']}; color: #fff; }}"
        )
        lay.addWidget(self._clear_btn)

        # Submit button
        self._submit_btn = QPushButton("Submit Order")
        self._submit_btn.setObjectName("PrimaryBtn")
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.setFixedHeight(38)
        self._submit_btn.setStyleSheet(
            f"QPushButton {{ background: {t['accent']}; color: #fff; "
            f"border: none; border-radius: 8px; padding: 0 24px; "
            f"font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {t['accent2']}; }}"
        )
        self._submit_btn.setEnabled(False)
        lay.addWidget(self._submit_btn)

        self._apply_theme()

    @property
    def clear_btn(self) -> QPushButton:
        return self._clear_btn

    @property
    def submit_btn(self) -> QPushButton:
        return self._submit_btn

    # ── Public API ────────────────────────────────────────────────

    def update_summary(self, item_count: int, total: float) -> None:
        self._count_lbl.setText(f"{item_count} item{'s' if item_count != 1 else ''}")
        self._total_lbl.setText(f"€{total:.2f}")
        self._submit_btn.setEnabled(item_count > 0)

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._apply_theme()

    def _apply_theme(self) -> None:
        t = self._tm.colors
        self.setStyleSheet(
            f"QWidget {{ background: {t['bg2']}; "
            f"border-top: 1px solid {t['border']}; }}"
        )
