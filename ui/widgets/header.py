from __future__ import annotations

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont, QPixmap

from core.app_state import get_state
from ui.widgets.togglebutton import ThemeToggle
from ui.widgets.language_switcher import LanguageSwitcher


class Header(QWidget):
    """
    show_back : bool
    show_kb_toggle : bool
        Show a virtual-keyboard toggle button.
    extra_buttons : list[tuple[str, callable]] | None
        Additional ghost buttons (label, slot) appended after the theme toggle.
    """

    back_requested = Signal()
    kb_toggled = Signal(bool)  # True = enabled

    def __init__(
        self,
        *,
        show_back: bool = False,
        show_kb_toggle: bool = False,
        extra_buttons: list[tuple[str, callable]] | None = None,
        parent: QWidget | None = None,
        main_window: None = None,
    ) -> None:
        super().__init__(parent)
        self._state = get_state()
        self._show_back = show_back
        self._show_kb = show_kb_toggle
        self._extra_buttons = extra_buttons or []
        self._ghost_btns: list[QPushButton] = []
        self._main_window = main_window

        self.setObjectName("Header")
        self.setFixedHeight(64)
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(32, 0, 32, 0)
        lay.setSpacing(20)

        # Logo
        pixmap = QPixmap("ui/assets/images/mediabridge.png")
        if not pixmap.isNull():
            scaled = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo = QLabel()
            logo.setPixmap(scaled)
            logo.setObjectName("LogoImage")
            lay.addWidget(logo)

        # Back button
        if self._show_back:
            self.back_btn = QPushButton("← Back")
            self.back_btn.setObjectName("GhostBtn")
            self.back_btn.setFixedHeight(36)
            self.back_btn.setFixedWidth(80)
            bf = QFont()
            bf.setPointSize(9)
            bf.setWeight(QFont.Medium)
            self.back_btn.setFont(bf)
            self.back_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.back_btn.clicked.connect(self.back_requested.emit)
            lay.addWidget(self.back_btn)
            self._ghost_btns.append(self.back_btn)

        lay.addStretch()

        # Language switcher
        is_dark = self._state.theme.is_dark if self._state.theme else True
        self.lang_select = LanguageSwitcher(is_dark=is_dark)
        lay.addWidget(self.lang_select)

        # KB toggle
        if self._show_kb:
            self.kb_toggle_btn = QPushButton("")
            self.kb_toggle_btn.setObjectName("GhostBtn")
            self.kb_toggle_btn.setFixedHeight(34)
            self.kb_toggle_btn.setFixedWidth(160)
            kbf = QFont()
            kbf.setPointSize(9)
            kbf.setWeight(QFont.Medium)
            self.kb_toggle_btn.setFont(kbf)
            self.kb_toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
            self.kb_toggle_btn.clicked.connect(self._on_kb_toggle)
            lay.addWidget(self.kb_toggle_btn)
            self._ghost_btns.append(self.kb_toggle_btn)
            self._sync_kb_label()

        # Theme toggle
        self.theme_toggle = ThemeToggle(is_dark=is_dark)
        self.theme_toggle.toggled.connect(self._on_theme_toggle)
        lay.addWidget(self.theme_toggle)

        # Extra ghost buttons
        for label, slot in self._extra_buttons:
            btn = QPushButton(label)
            btn.setObjectName("GhostBtn")
            btn.setFixedHeight(34)
            btn.setFixedWidth(72)
            bf2 = QFont()
            bf2.setPointSize(9)
            bf2.setWeight(QFont.Medium)
            btn.setFont(bf2)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(slot)
            lay.addWidget(btn)
            self._ghost_btns.append(btn)

    # ── Theme sync ────────────────────────────────────────────────────────────
    def sync_theme(self) -> None:
        if self._state.theme:
            is_dark = self._state.theme.is_dark
            self.theme_toggle.blockSignals(True)
            self.theme_toggle.set_state(is_dark)
            self.theme_toggle.blockSignals(False)
            self.lang_select.set_theme(is_dark)

    def _on_theme_toggle(self, is_dark: bool) -> None:
        if self._state.theme:
            self._state.theme.set_dark(is_dark)
        try:
            self._state.set("is_dark", is_dark)
        except Exception:
            pass
        self.lang_select.set_theme(is_dark)

    # ── KB toggle ─────────────────────────────────────────────────────────────
    def _on_kb_toggle(self) -> None:
        new_state = not self._main_window.is_virtual_keyboard_enabled()
        self._main_window.set_virtual_keyboard_enabled(new_state)
        self._sync_kb_label(new_state)

    def _sync_kb_label(self, enabled: bool | None = None) -> None:
        if not self._show_kb:
            return
        if enabled is None:             
            from main import MainWindow
            win = self.window()
            enabled = True
            if isinstance(win, MainWindow):
                enabled = win.is_virtual_keyboard_enabled()
        self.kb_toggle_btn.setText(f"Virtual Keyboard: {'ON' if enabled else 'OFF'}")
        self.kb_toggle_btn.setStyleSheet(f"QPushButton {{ background-color: {'#3B6FD4' if enabled else 'transparent'};color: {'#EEF0F8' if enabled else '#8B90A8'}; }}")



    def sync_kb_state(self) -> None:
        self._sync_kb_label()
