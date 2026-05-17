from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from ui.themes.theme import ThemeManager


class NavTabs(QWidget):
    """
    Simple themed navbar using ONLY Qt stylesheets.
    No custom painting.
    No paintEvent.
    No animations.

    Usage
    -----
    tabs = NavTabs(
        [
            ("display", "Display"),
            ("behavior", "Behavior"),
            ("header", "Header"),
            ("mapping", "Field Map"),
        ],
        tm
    )

    tabs.tab_changed.connect(...)
    """

    tab_changed = Signal(str)

    def __init__(
        self,
        tabs: list[tuple[str, str]],
        tm: ThemeManager,
        parent=None,
    ):
        super().__init__(parent)

        self._tm = tm
        self._buttons: dict[str, QPushButton] = {}

        self.setObjectName("NavTabs")
        self.setFixedHeight(30)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, label in tabs:
            btn = QPushButton(label)

            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

            btn.setObjectName("NavTabButton")

            btn.setMinimumHeight(30)
            btn.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            btn.clicked.connect(
                lambda checked=False, k=key: self._on_clicked(k)
            )

            self._group.addButton(btn)

            self._buttons[key] = btn
            layout.addWidget(btn)

        # activate first tab
        if tabs:
            self.set_active(tabs[0][0])

    # ------------------------------------------------------------------

    def set_active(self, key: str) -> None:
        if key not in self._buttons:
            return

        self._buttons[key].setChecked(True)

    # ------------------------------------------------------------------

    def _on_clicked(self, key: str) -> None:
        self.tab_changed.emit(key)

