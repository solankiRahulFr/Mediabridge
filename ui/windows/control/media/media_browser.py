from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize, QTimer, QRunnable, QThreadPool, QObject
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QFrame,
)

from ui.themes.theme import ThemeManager
from ui.widgets.touch_scroll import TouchScrollArea

log = logging.getLogger(__name__)

# ── Type icons / colors ──────────────────────────────────────────────────────
_TYPE_ICON = {"image": "image", "video": "video", "pdf": "pdf"}
_TYPE_COLOR = {"image": "#32246F8F", "video": "#32246F8F", "pdf": "#32246F8F"}

_THUMB_W = 160
_THUMB_H = 120
_CARD_W  = 170
_CARD_H  = 185
_THUMB_BATCH = 12 


# Thumbnail loader (background thread)
class _ThumbSignals(QObject):
    done = Signal(int, QPixmap)  # (card_index, pixmap)


class _ThumbTask(QRunnable):

    def __init__(self, card_index: int, path: str) -> None:
        super().__init__()
        self.signals = _ThumbSignals()
        self._idx = card_index
        self._path = path
        self.setAutoDelete(True)

    def run(self) -> None:
        px = QPixmap(self._path)
        if not px.isNull():
            px = px.scaled(_THUMB_W, _THUMB_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.signals.done.emit(self._idx, px)


# Media Card
class _MediaCard(QFrame):

    clicked = Signal(int)  # emits record index

    def __init__(
        self, record: dict, index: int, tm: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._record = record
        self._index = index
        self._tm = tm

        self.setFixedSize(_CARD_W, _CARD_H)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("MediaCard")

        self._build()
        self._apply_style()

    def _build(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        ct = self._record.get("content_type", "")

        # Thumbnail — start with icon placeholder (instant)
        self._thumb = QLabel()
        self._thumb.setFixedSize(_THUMB_W, _THUMB_H)
        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setStyleSheet("background: rgba(0,0,0,0.3); border-radius: 6px;")
        self._set_icon_placeholder(ct)
        lay.addWidget(self._thumb, alignment=Qt.AlignCenter)

        # Title + type badge row
        info = QHBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(2, 0, 2, 0)

        title = self._record.get("title", "Untitled")
        if len(title) > 18:
            title = title[:16] + "…"
        title_lbl = QLabel(title)
        title_lbl.setStatusTip(self._record.get("title", "Untitled"))
        title_lbl.setObjectName("CardTitle")
        title_lbl.setStyleSheet("background: transparent;")
        info.addWidget(title_lbl, 1)

        lay.addLayout(info)
        

        badge = QLabel(_TYPE_ICON.get(ct, "media"), self._thumb)
        badge.setFixedSize(40, 20)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background: {_TYPE_COLOR.get(ct, '#888')}; color: white; "
            f"border-radius: 4px; font-size: 10px;"
        )
        badge.move(5,5)
        badge.raise_()
        badge.show()


    def set_thumbnail(self, px: QPixmap) -> None:
        """Called from the async loader once the thumbnail is ready."""
        if not px.isNull():
            self._thumb.setPixmap(px)

    def thumb_source(self) -> str:
        """Return the best path to use for thumbnail generation."""
        ct = self._record.get("content_type", "")
        thumb = self._record.get("thumbnail", "")
        if thumb and Path(thumb).is_file():
            return thumb
        if ct == "image":
            img = self._record.get("image", "")
            if img and Path(img).is_file():
                return img
        return ""

    def _set_icon_placeholder(self, ct: str) -> None:
        icon = _TYPE_ICON.get(ct, "📁")
        self._thumb.setText(icon)
        font = QFont()
        font.setPointSize(32)
        self._thumb.setFont(font)

    def _apply_style(self) -> None:
        c = self._tm.colors
        self.setStyleSheet(
            f"QFrame#MediaCard {{"
            f"  background: {c['surface']}; border: 1px solid {c['border']};"
            f"  border-radius: 8px;"
            f"}}"
            f"QFrame#MediaCard:hover {{"
            f"  border-color: {c['accent']}; background: {c['surface2']};"
            f"}}"
            f"QLabel#CardTitle {{"
            f"  color: {c['text']}; font-size: 11px;"
            f"}}"
        )

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._index)
        event.accept()


# Filter chip
class _FilterChip(QPushButton):
    def __init__(self, label: str, filter_key: str, tm: ThemeManager, parent=None):
        super().__init__(label, parent)
        self.filter_key = filter_key
        self._tm = tm
        self._active = False
        self.setFixedHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setChecked(active)
        self._apply_style()

    def _apply_style(self) -> None:
        c = self._tm.colors
        if self._active:
            self.setStyleSheet(
                f"QPushButton {{ background: {c['accent']}; color: #fff; "
                f"border: none; border-radius: 14px; padding: 4px 14px; font-weight: bold; font-size: 12px; }}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{ background: {c['surface2']}; color: {c['text2']}; "
                f"border: 1px solid {c['border']}; border-radius: 14px; padding: 4px 14px; font-size: 12px; }}"
                f"QPushButton:hover {{ border-color: {c['accent']}; color: {c['text']}; }}"
            )


# Media Browser (gallery grid)
class MediaBrowser(QWidget):
    media_selected = Signal(int)

    def __init__(self, tm: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tm = tm
        self._records: list[dict] = []
        self._filtered: list[tuple[int, dict]] = []  # (original_idx, record)
        self._filter_type = "all"
        self._search_text = ""
        self._cards: list[_MediaCard] = []
        self._thumb_pool = QThreadPool.globalInstance()
        self._last_cols = 0

        self._build()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._apply_filters)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 0)
        root.setSpacing(8)

        # ── Top bar: search + filters ─────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search media…")
        self._search.setObjectName("MediaSearch")
        self._search.setFixedHeight(36)
        self._search.textChanged.connect(lambda _: self._search_timer.start())
        top.addWidget(self._search, 1)

        # Filter chips
        self._chips: list[_FilterChip] = []
        for label, key in [("All", "all"), ("🖼 Images", "image"), ("🎬 Videos", "video"), ("📄 PDFs", "pdf")]:
            chip = _FilterChip(label, key, self._tm)
            chip.clicked.connect(lambda _, k=key: self._set_filter(k))
            top.addWidget(chip)
            self._chips.append(chip)
        self._chips[0].set_active(True)

        root.addLayout(top)

        # ── Count label ───────────────────────────────────────────
        self._count_lbl = QLabel("")
        self._count_lbl.setObjectName("CountLabel")
        self._count_lbl.setStyleSheet(
            f"color: {self._tm.colors['text3']}; font-size: 11px; background: transparent; padding-left: 4px;"
        )
        root.addWidget(self._count_lbl)

        # ── Scrollable grid area ──────────────────────────────────
        self._scroll = TouchScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(10)
        self._grid_layout.setContentsMargins(4, 4, 4, 4)
        self._scroll.setWidget(self._grid_widget)

        root.addWidget(self._scroll, 1)

        self._apply_theme()

    # ── Public API ────────────────────────────────────────────────

    def set_records(self, records: list[dict]) -> None:
        self._records = records
        self._apply_filters()

    def update_theme(self, tm: ThemeManager) -> None:
        self._tm = tm
        self._apply_theme()
        self._apply_filters()

    # ── Filters ───────────────────────────────────────────────────

    def _set_filter(self, filter_type: str) -> None:
        self._filter_type = filter_type
        for chip in self._chips:
            chip.set_active(chip.filter_key == filter_type)
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self._search.text().strip().lower()
        self._search_text = query
        ft = self._filter_type

        self._filtered = []
        for i, rec in enumerate(self._records):
            # Type filter
            if ft != "all" and rec.get("content_type") != ft:
                continue
            # Search filter
            if query:
                title = (rec.get("title") or "").lower()
                tags = " ".join(rec.get("tags") or []).lower()
                desc = (rec.get("description") or "").lower()
                if query not in title and query not in tags and query not in desc:
                    continue
            self._filtered.append((i, rec))

        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        # Clear existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Calculate columns based on available width
        avail = self._scroll.viewport().width() or 800
        cols = max(2, avail // (_CARD_W + 10))
        self._last_cols = cols

        for pos, (orig_idx, rec) in enumerate(self._filtered):
            card = _MediaCard(rec, orig_idx, self._tm)
            card.clicked.connect(self.media_selected.emit)
            row = pos // cols
            col = pos % cols
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)

        # Update count
        total = len(self._records)
        shown = len(self._filtered)
        if self._filter_type == "all" and not self._search_text:
            self._count_lbl.setText(f"{total} media items")
        else:
            self._count_lbl.setText(f"Showing {shown} of {total}")

        # Kick off async thumbnail loading
        self._load_thumbnails_async()

    def _load_thumbnails_async(self) -> None:
        for i, card in enumerate(self._cards):
            src = card.thumb_source()
            if not src:
                continue
            task = _ThumbTask(i, src)
            task.signals.done.connect(self._on_thumb_ready)
            self._thumb_pool.start(task)

    def _on_thumb_ready(self, card_index: int, px: QPixmap) -> None:
        if 0 <= card_index < len(self._cards):
            self._cards[card_index].set_thumbnail(px)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Only rebuild if column count actually changed
        avail = self._scroll.viewport().width() or 800
        cols = max(2, avail // (_CARD_W + 10))
        if cols != self._last_cols and self._filtered:
            self._rebuild_grid()

    # ── Theme ─────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        c = self._tm.colors
        self.setStyleSheet(
            f"QLineEdit#MediaSearch {{"
            f"  background: {c['surface']}; color: {c['text']};"
            f"  border: 1px solid {c['border']}; border-radius: 8px;"
            f"  padding: 4px 12px; font-size: 13px;"
            f"}}"
            f"QLineEdit#MediaSearch:focus {{"
            f"  border-color: {c['accent']};"
            f"}}"
        )
