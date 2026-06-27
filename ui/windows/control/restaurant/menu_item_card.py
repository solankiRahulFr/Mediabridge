
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager

logger = logging.getLogger(__name__)

_CARD_W = 260
_CARD_H = 320


class MenuItemCard(QFrame):
    quantity_changed = Signal(str, int)
    customisation_changed = Signal(str, str)

    def __init__(self, item: dict, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._tm = tm
        self._qty = 0

        self.setObjectName("MenuCard")
        self.setFixedSize(_CARD_W, _CARD_H)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()
        self._refresh_style()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Image area
        self._img_lbl = QLabel()
        self._img_lbl.setFixedHeight(120)
        self._img_lbl.setAlignment(Qt.AlignCenter)
        self._img_lbl.setStyleSheet("background: #0D0F14; border-radius: 12px 12px 0 0;")

        img_path = self._item.get("image", "")
        if img_path and not img_path.startswith("http"):
            px = QPixmap(img_path)
            if not px.isNull():
                self._img_lbl.setPixmap(
                    px.scaled(_CARD_W, 120, Qt.KeepAspectRatioByExpanding,
                              Qt.SmoothTransformation)
                )
            else:
                self._set_placeholder()
        else:
            self._set_placeholder()
        lay.addWidget(self._img_lbl)

        # Info section
        info = QWidget()
        info.setObjectName("CardInfo")
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(12, 8, 12, 8)
        info_lay.setSpacing(4)

        # Name
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setWeight(QFont.DemiBold)
        self._name_lbl = QLabel(self._item.get("name", ""))
        self._name_lbl.setFont(name_font)
        self._name_lbl.setWordWrap(True)
        self._name_lbl.setMaximumHeight(36)
        info_lay.addWidget(self._name_lbl)

        # Price + Category
        price = self._item.get("price", 0)
        cat = self._item.get("category", "")
        meta_lbl = QLabel(f"€{price:.2f}  ·  {cat}")
        meta_lbl.setStyleSheet(
            f"font-size: 10px; color: {self._tm.color('accent')}; background: transparent;"
        )
        info_lay.addWidget(meta_lbl)

        # Description (truncated)
        desc = self._item.get("description", "")
        if desc:
            desc_lbl = QLabel(desc[:60] + ("…" if len(desc) > 60 else ""))
            desc_lbl.setStyleSheet(
                f"font-size: 9px; color: {self._tm.color('text3')}; background: transparent;"
            )
            desc_lbl.setWordWrap(True)
            desc_lbl.setMaximumHeight(28)
            info_lay.addWidget(desc_lbl)

        lay.addWidget(info, 1)

        # Quantity controls
        qty_row = QHBoxLayout()
        qty_row.setContentsMargins(12, 4, 12, 4)
        qty_row.setSpacing(6)

        self._minus_btn = QPushButton("−")
        self._minus_btn.setFixedSize(28, 28)
        self._minus_btn.setCursor(Qt.PointingHandCursor)
        self._minus_btn.clicked.connect(self._decrement)
        qty_row.addWidget(self._minus_btn)

        self._qty_lbl = QLabel("0")
        self._qty_lbl.setAlignment(Qt.AlignCenter)
        self._qty_lbl.setFixedWidth(30)
        self._qty_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {self._tm.color('text')}; "
            f"background: transparent;"
        )
        qty_row.addWidget(self._qty_lbl)

        self._plus_btn = QPushButton("+")
        self._plus_btn.setFixedSize(28, 28)
        self._plus_btn.setCursor(Qt.PointingHandCursor)
        self._plus_btn.clicked.connect(self._increment)
        qty_row.addWidget(self._plus_btn)

        qty_row.addStretch()

        self._del_btn = QPushButton("🗑")
        self._del_btn.setFixedSize(28, 28)
        self._del_btn.setCursor(Qt.PointingHandCursor)
        self._del_btn.setToolTip("Remove from order")
        self._del_btn.clicked.connect(self._remove)
        qty_row.addWidget(self._del_btn)

        lay.addLayout(qty_row)

        # Customisation input (hidden until qty > 0)
        self._custom_input = QLineEdit()
        self._custom_input.setPlaceholderText("Special instructions…")
        self._custom_input.setFixedHeight(28)
        self._custom_input.setStyleSheet(
            f"QLineEdit {{ background: {self._tm.color('surface2')}; "
            f"color: {self._tm.color('text')}; border: 1px solid {self._tm.color('border')}; "
            f"border-radius: 6px; padding: 0 8px; font-size: 10px; }}"
        )
        self._custom_input.textChanged.connect(
            lambda text: self.customisation_changed.emit(self._item["id"], text)
        )
        self._custom_input.setVisible(False)
        lay.addWidget(self._custom_input)

    def _set_placeholder(self) -> None:
        self._img_lbl.setText("🍽")
        font = QFont()
        font.setPointSize(32)
        self._img_lbl.setFont(font)

    # ── Quantity ──────────────────────────────────────────────────

    def _increment(self) -> None:
        self._qty += 1
        self._update_qty()

    def _decrement(self) -> None:
        if self._qty > 0:
            self._qty -= 1
            self._update_qty()

    def _remove(self) -> None:
        self._qty = 0
        self._custom_input.clear()
        self._update_qty()

    def _update_qty(self) -> None:
        self._qty_lbl.setText(str(self._qty))
        self._custom_input.setVisible(self._qty > 0)
        self._refresh_style()
        self.quantity_changed.emit(self._item["id"], self._qty)

    # ── Public API ────────────────────────────────────────────────

    @property
    def item_id(self) -> str:
        return self._item.get("id", "")

    @property
    def quantity(self) -> int:
        return self._qty

    def set_quantity(self, qty: int) -> None:
        self._qty = max(0, qty)
        self._qty_lbl.setText(str(self._qty))
        self._custom_input.setVisible(self._qty > 0)
        self._refresh_style()

    @property
    def customisation(self) -> str:
        return self._custom_input.text()

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._refresh_style()

    def _refresh_style(self) -> None:
        t = self._tm.colors
        border = t["accent"] if self._qty > 0 else t["border"]
        self.setStyleSheet(
            f"QFrame#MenuCard {{"
            f"  background: {t['surface']}; border: 2px solid {border};"
            f"  border-radius: 12px;"
            f"}}"
            f"QWidget#CardInfo {{ background: transparent; }}"
        )
        # Qty button styles
        for btn in (self._minus_btn, self._plus_btn):
            btn.setStyleSheet(
                f"QPushButton {{ background: {t['surface2']}; color: {t['text']}; "
                f"border: 1px solid {t['border']}; border-radius: 6px; font-size: 14px; font-weight: bold; }}"
                f"QPushButton:hover {{ background: {t['accent']}; color: #fff; border-color: {t['accent']}; }}"
            )
        self._del_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {t['danger']}; border-radius: 6px; }}"
        )
