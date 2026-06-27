
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QLineEdit,
    QScrollArea, QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager
from ui.windows.control.restaurant.menu_item_card import MenuItemCard

logger = logging.getLogger(__name__)

_COLUMNS = 3


class MenuGrid(QWidget):
    quantity_changed = Signal(str, int)
    customisation_changed = Signal(str, str)

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._all_items: list[dict] = []
        self._cards: list[MenuItemCard] = []
        self._active_category = "all"
        self._active_diet = "all"
        self._search_query = ""

        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        # Search bar
        t = self._tm.colors
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search menu…")
        self._search.setFixedHeight(38)
        self._search.setStyleSheet(
            f"QLineEdit {{ background: {t['surface2']}; color: {t['text']}; "
            f"border: 1px solid {t['border']}; border-radius: 10px; "
            f"padding: 0 14px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {t['accent']}; }}"
        )
        self._search.textChanged.connect(self._on_search)
        root.addWidget(self._search)

        # Scroll area with grid
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._grid.setSpacing(12)
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

        # Empty state
        self._empty_lbl = QLabel("No items found")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {self._tm.color('text3')}; font-size: 14px;"
        )
        self._empty_lbl.hide()
        root.addWidget(self._empty_lbl)

    # ── Public API ────────────────────────────────────────────────

    def set_items(self, items: list[dict]) -> None:
        self._all_items = items
        self._rebuild()

    def filter_by_category(self, category: str) -> None:
        self._active_category = category
        self._rebuild()

    def filter_by_diet(self, diet: str) -> None:
        self._active_diet = diet
        self._rebuild()

    def get_order(self) -> list[dict]:
        order = []
        for card in self._cards:
            if card.quantity > 0:
                order.append({
                    "id": card.item_id,
                    "name": card._item.get("name", ""),
                    "price": card._item.get("price", 0),
                    "quantity": card.quantity,
                    "customisation": card.customisation,
                })
        return order

    def clear_order(self) -> None:
        for card in self._cards:
            card.set_quantity(0)

    def get_total(self) -> float:
        return sum(
            card._item.get("price", 0) * card.quantity
            for card in self._cards if card.quantity > 0
        )

    def get_item_count(self) -> int:
        return sum(card.quantity for card in self._cards if card.quantity > 0)

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        for card in self._cards:
            card.update_theme(tm)
        t = tm.colors
        self._search.setStyleSheet(
            f"QLineEdit {{ background: {t['surface2']}; color: {t['text']}; "
            f"border: 1px solid {t['border']}; border-radius: 10px; "
            f"padding: 0 14px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {t['accent']}; }}"
        )

    # ── Internals ─────────────────────────────────────────────────

    def _on_search(self, text: str) -> None:
        self._search_query = text.strip().lower()
        self._rebuild()

    def _rebuild(self) -> None:
        # Clear existing
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filter items
        filtered = self._all_items

        if self._active_category != "all":
            filtered = [i for i in filtered
                        if i.get("category", "") == self._active_category]

        if self._active_diet != "all":
            filtered = [i for i in filtered
                        if self._active_diet in i.get("tags", [])]

        if self._search_query:
            filtered = [i for i in filtered
                        if self._search_query in (i.get("name") or "").lower()
                        or self._search_query in (i.get("description") or "").lower()]

        # Only available items
        filtered = [i for i in filtered if i.get("available", True)]

        if not filtered:
            self._empty_lbl.show()
            return

        self._empty_lbl.hide()
        for idx, item in enumerate(filtered):
            card = MenuItemCard(item, self._tm)
            card.quantity_changed.connect(self.quantity_changed)
            card.customisation_changed.connect(self.customisation_changed)
            row, col = divmod(idx, _COLUMNS)
            self._grid.addWidget(card, row, col)
            self._cards.append(card)
