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
from core.app_state import get_state


class NavTabs(QWidget):
    """
    tabs = NavTabs(
        [
            ("display", "nav.display"),
            ("behavior", "nav.behavior"),
            ("header", "nav.header"),
            ("mapping", "nav.mapping"),
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
        self._state = get_state()
        self._buttons: dict[str, QPushButton] = {}
        self._tab_keys: dict[str, str] = {}  # Maps button key to i18n key

        self.setObjectName("NavTabs")
        self.setFixedHeight(40)
        self.setAutoFillBackground(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, i18n_key in tabs:
            # Translate the key to get the label text
            label = self._state.lang.t(i18n_key)
            btn = QPushButton(label)

            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)

            btn.setObjectName("NavTabButton")

            btn.setMinimumHeight(38)
            btn.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            btn.clicked.connect(
                lambda checked=False, k=key: self._on_clicked(k)
            )

            self._group.addButton(btn)

            self._buttons[key] = btn
            self._tab_keys[key] = i18n_key
            layout.addWidget(btn)

        # Listen for language changes
        self._state.lang.on_change(lambda _code: self._retranslate())

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

    # ------------------------------------------------------------------

    def _retranslate(self) -> None:
        """Update all tab labels from current language."""
        for key, btn in self._buttons.items():
            i18n_key = self._tab_keys[key]
            btn.setText(self._state.lang.t(i18n_key))

