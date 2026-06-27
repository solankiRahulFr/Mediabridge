
from __future__ import annotations

import logging
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from core.app_state import AppState
from ui.themes.theme import ThemeManager
from ui.widgets.togglebutton import ThemeToggle
from ui.windows.control.restaurant.category_sidebar import CategorySidebar
from ui.windows.control.restaurant.menu_grid import MenuGrid
from ui.windows.control.restaurant.menu_loader import (
    get_categories, load_menu,
)
from ui.windows.control.restaurant.order_bar import OrderBar

logger = logging.getLogger(__name__)

_EXIT_TAP_COUNT    = 6
_EXIT_TAP_WINDOW_S = 3.0


class RestaurantWindow(QWidget):

    order_submitted = Signal(list)
    exit_requested = Signal()

    def __init__(
        self,
        tm: ThemeManager | None = None,
        menu_source: str | None = None,
        restaurant_cfg: dict | None = None,
        on_exit: callable | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tm = tm or AppState.instance().theme_manager
        self._state = AppState.instance()
        self._cfg = restaurant_cfg or {}
        self._menu_source = menu_source
        self._on_exit = on_exit
        self._exit_taps: list[float] = []

        self.setWindowTitle(
            self._cfg.get("restaurant_name", "MediaBridge — Restaurant")
        )

        self._build()
        self._connect_signals()

        # Load menu data
        if menu_source:
            self._load_menu(menu_source)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(self._build_header())

        # Body: sidebar + grid
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = CategorySidebar(self._tm)
        body.addWidget(self._sidebar)

        # Main content area
        content = QVBoxLayout()
        content.setContentsMargins(16, 12, 16, 0)
        content.setSpacing(0)

        self._grid = MenuGrid(self._tm)
        content.addWidget(self._grid, 1)

        body.addLayout(content, 1)
        root.addLayout(body, 1)

        # Order bar
        self._order_bar = OrderBar(self._tm)
        root.addWidget(self._order_bar)

        self._tm.apply(self)

    def _build_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("RestHeader")
        hdr.setFixedHeight(self._cfg.get("header_height", 64))

        hdr_bg = self._cfg.get("header_bg", self._tm.color("bg2"))
        hdr_color = self._cfg.get("header_color", self._tm.color("text"))
        hdr.setStyleSheet(
            f"QFrame#RestHeader {{ background: {hdr_bg}; "
            f"border-bottom: 1px solid {self._tm.color('border')}; }}"
        )
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(20, 0, 20, 0)

        # Exit gesture area (invisible)
        self._exit_zone = QLabel()
        self._exit_zone.setFixedSize(48, 48)
        self._exit_zone.setStyleSheet("background: transparent;")
        self._exit_zone.mousePressEvent = self._on_exit_tap
        lay.addWidget(self._exit_zone)

        # Logo
        logo_url = self._cfg.get("logo_url", "")
        if logo_url and not logo_url.startswith("http"):
            px = QPixmap(logo_url)
            if not px.isNull():
                logo_img = QLabel()
                logo_img.setPixmap(
                    px.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                lay.addWidget(logo_img)
                lay.addSpacing(12)

        # Restaurant name
        name = self._cfg.get("restaurant_name", "Restaurant")
        title_font = QFont()
        title_font.setPointSize(self._cfg.get("title_font_size", 16))
        title_font.setWeight(QFont.Bold)
        title_lbl = QLabel(name)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(f"color: {hdr_color}; background: transparent;")
        lay.addWidget(title_lbl)

        lay.addStretch()

        # Theme toggle (optional)
        if self._cfg.get("show_theme_toggle", False):
            self._theme_toggle = ThemeToggle(is_dark=self._tm.is_dark)
            self._theme_toggle.toggled.connect(self._on_theme_toggle)
            lay.addWidget(self._theme_toggle)

        return hdr

    def _connect_signals(self) -> None:
        self._sidebar.category_selected.connect(self._grid.filter_by_category)
        self._sidebar.diet_filter_changed.connect(self._grid.filter_by_diet)
        self._grid.quantity_changed.connect(self._on_qty_changed)
        self._order_bar.clear_btn.clicked.connect(self._clear_order)
        self._order_bar.submit_btn.clicked.connect(self._submit_order)

    # ── Menu loading ──────────────────────────────────────────────

    def _load_menu(self, source: str) -> None:
        items = load_menu(source)
        if not items:
            logger.warning("No menu items loaded from: %s", source)
            return
        logger.info("Loaded %d menu items from: %s", len(items), source)
        self._grid.set_items(items)
        categories = get_categories(items)
        self._sidebar.set_categories(categories)

    def reload_menu(self, source: str | None = None) -> None:
        src = source or self._menu_source
        if src:
            self._load_menu(src)

    # ── Order management ──────────────────────────────────────────

    def _on_qty_changed(self, item_id: str, qty: int) -> None:
        self._order_bar.update_summary(
            self._grid.get_item_count(),
            self._grid.get_total(),
        )

    def _clear_order(self) -> None:
        self._grid.clear_order()
        self._order_bar.update_summary(0, 0.0)

    def _submit_order(self) -> None:
        order = self._grid.get_order()
        if order:
            logger.info("Order submitted: %d items, total €%.2f",
                        len(order), self._grid.get_total())
            self.order_submitted.emit(order)
            self._clear_order()

    # ── Exit gesture ──────────────────────────────────────────────

    def _on_exit_tap(self, _) -> None:
        now = time.monotonic()
        self._exit_taps = [t for t in self._exit_taps if now - t < _EXIT_TAP_WINDOW_S]
        self._exit_taps.append(now)
        if len(self._exit_taps) >= _EXIT_TAP_COUNT:
            self._exit_taps.clear()
            logger.info("Restaurant exit gesture triggered")
            self.exit_requested.emit()
            if self._on_exit:
                self._on_exit()

    # ── Theme ─────────────────────────────────────────────────────

    def _on_theme_toggle(self, is_dark: bool) -> None:
        self._tm.set_dark(is_dark)
        self._state.set("is_dark", is_dark)
        self._tm.apply(self)
        self._sidebar.update_theme(self._tm)
        self._grid.update_theme(self._tm)
        self._order_bar.update_theme(self._tm)

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._tm.apply(self)
        self._sidebar.update_theme(tm)
        self._grid.update_theme(tm)
        self._order_bar.update_theme(tm)
