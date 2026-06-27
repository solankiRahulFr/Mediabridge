
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ui.themes.theme import ThemeManager

logger = logging.getLogger(__name__)


class CategorySidebar(QWidget):

    category_selected = Signal(str)      # category name or "all"
    diet_filter_changed = Signal(str)    # "all" | "veg" | "non-veg"

    def __init__(self, tm: ThemeManager,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._active_category = "all"
        self._active_diet = "all"
        self._cat_buttons: dict[str, QPushButton] = {}

        self.setFixedWidth(200)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        t = self._tm.colors

        # Diet filter tabs
        diet_frame = QFrame()
        diet_frame.setObjectName("DietFilter")
        diet_frame.setStyleSheet(
            f"QFrame#DietFilter {{ background: {t['bg2']}; "
            f"border-bottom: 1px solid {t['border']}; }}"
        )
        diet_lay = QVBoxLayout(diet_frame)
        diet_lay.setContentsMargins(8, 12, 8, 12)
        diet_lay.setSpacing(6)

        title = QLabel("Filter")
        title.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {t['text2']}; "
            f"background: transparent;"
        )
        diet_lay.addWidget(title)

        self._diet_btns: dict[str, QPushButton] = {}
        for key, label in [("all", "🍽  All"), ("veg", "🥬  Veg"), ("non-veg", "🍖  Non-Veg")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, k=key: self._on_diet(k))
            diet_lay.addWidget(btn)
            self._diet_btns[key] = btn
        self._diet_btns["all"].setChecked(True)
        root.addWidget(diet_frame)

        # Category list
        cat_title = QLabel("Categories")
        cat_title.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {t['text2']}; "
            f"background: transparent; padding: 12px 8px 4px 8px;"
        )
        root.addWidget(cat_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        self._cat_container = QWidget()
        self._cat_lay = QVBoxLayout(self._cat_container)
        self._cat_lay.setContentsMargins(8, 4, 8, 8)
        self._cat_lay.setSpacing(4)
        self._cat_lay.addStretch()
        scroll.setWidget(self._cat_container)
        root.addWidget(scroll, 1)

        self._refresh_styles()

    def set_categories(self, categories: list[str]) -> None:
        """Populate category buttons."""
        for btn in self._cat_buttons.values():
            btn.deleteLater()
        self._cat_buttons.clear()

        while self._cat_lay.count():
            item = self._cat_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # "All" button
        all_btn = QPushButton("📋  All")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.setCursor(Qt.PointingHandCursor)
        all_btn.setFixedHeight(36)
        all_btn.clicked.connect(lambda: self._on_category("all"))
        self._cat_buttons["all"] = all_btn
        self._cat_lay.addWidget(all_btn)

        for cat in categories:
            btn = QPushButton(cat)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda _, c=cat: self._on_category(c))
            self._cat_buttons[cat] = btn
            self._cat_lay.addWidget(btn)

        self._cat_lay.addStretch()
        self._refresh_styles()

    def _on_diet(self, key: str) -> None:
        self._active_diet = key
        for k, btn in self._diet_btns.items():
            btn.setChecked(k == key)
        self._refresh_styles()
        self.diet_filter_changed.emit(key)

    def _on_category(self, cat: str) -> None:
        self._active_category = cat
        for k, btn in self._cat_buttons.items():
            btn.setChecked(k == cat)
        self._refresh_styles()
        self.category_selected.emit(cat)

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        t = self._tm.colors

        self.setStyleSheet(
            f"QWidget {{ background: {t['surface']}; }}"
        )

        for key, btn in self._diet_btns.items():
            active = key == self._active_diet
            if active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {t['accent']}; color: #fff; "
                    f"border: none; border-radius: 6px; font-size: 11px; font-weight: bold; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {t['surface2']}; color: {t['text2']}; "
                    f"border: 1px solid {t['border']}; border-radius: 6px; font-size: 11px; }}"
                    f"QPushButton:hover {{ border-color: {t['accent']}; color: {t['text']}; }}"
                )

        for key, btn in self._cat_buttons.items():
            active = key == self._active_category
            if active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {t['accent']}; color: #fff; "
                    f"border: none; border-radius: 8px; font-size: 12px; "
                    f"font-weight: bold; text-align: left; padding-left: 12px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {t['text']}; "
                    f"border: none; border-radius: 8px; font-size: 12px; "
                    f"text-align: left; padding-left: 12px; }}"
                    f"QPushButton:hover {{ background: {t['surface2']}; }}"
                )
