import pathlib

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QListView,
    QStyledItemDelegate,
)

from core.app_state import get_state

# Base path for resolving flag image assets
_BASE_PATH = pathlib.Path(__file__).resolve().parent.parent.parent


class LanguageSwitcher(QComboBox):
    def __init__(self, is_dark=True, parent=None):
        super().__init__(parent)
        self._state = get_state()
        self._dark = is_dark
 
        # Main widget setup
        self.setFixedSize(95, 34)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFocusPolicy(Qt.StrongFocus)

  
        # This removes the white top/bottom background issue
        self.setStyleSheet(
            """
            QComboBox {
                combobox-popup: 1;
            }
            """
        )

        # Custom view
        view = QListView()
        self.setView(view)
        view.setItemDelegate(QStyledItemDelegate())
        view.setFrameShape(QFrame.NoFrame)
        view.setCursor(QCursor(Qt.PointingHandCursor))
        view.setSpacing(0)
        view.setContentsMargins(0, 0, 0, 0)
        view.viewport().setContentsMargins(0, 0, 0, 0)
        view.setMinimumWidth(120)
        view.setMaximumWidth(120)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setAutoFillBackground(False)
        view.viewport().setAutoFillBackground(False)
        view.viewport().setAttribute(Qt.WA_StyledBackground, True)

        # signals
        self.currentIndexChanged.connect(self._on_language_changed)

        # Load languages from central LanguageManager
        languages = self._state.lang.available()
        for lang in languages:
            flag_path = str(_BASE_PATH / "ui" / "assets" / "images" / "flags" / lang["flag"])
            flag = QIcon(flag_path).pixmap(16, 16)
            self.addItem(flag, lang["name"], userData=lang["code"])

        current_code = self._state.lang.current
        if current_code:
            index = self.findData(current_code)
            if index != -1:
                self.setCurrentIndex(index)

        # Apply theme
        self.apply_theme()
    def hidePopup(self):
        super().hidePopup()

    # Functionality
    def _on_language_changed(self, index):
        lang_code = self.itemData(index)
        if lang_code and self._state.lang:
            self._state.lang.set_language(lang_code)

    # Theme — reads tokens from central ThemeManager
    def _get_colors(self) -> dict[str, str]:
        if self._state.theme:
            return self._state.theme.colors
        # Fallback to THEMES dict directly if manager not yet initialised
        from ui.themes.theme import THEMES
        return THEMES["dark" if self._dark else "light"]

    def apply_theme(self):
        t = self._get_colors()

        self.setStyleSheet(f"""

        QComboBox {{
            combobox-popup: 1;

            background-color: transparent;
            color: {t['text2']};

            border: 1.5px solid {t['border']};
            border-radius: 8px;

            padding: 4px 8px;

            min-height: 24px;
        }}

        QComboBox:hover {{
            border-color: {t['accent']};
            background-color: {t['surface2']};
            color: {t['text']};
        }}

        QComboBox::drop-down {{
            border: none;
            background: transparent;
            width: 0px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border: none;
            width: 0px;
            height: 0px;
        }}


        QComboBox QListView {{
            background-color: {t['surface']};

            border: none;
            outline: none;

            padding: 0px;
            margin: 0px;

            border-radius: 8px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {t['surface']};

            border: none;
            outline: none;

            padding: 0px;
            margin: 0px;

            selection-background-color: transparent;
        }}

        /* VERY IMPORTANT */
        QComboBox QAbstractItemView::viewport {{
            background-color: {t['surface']};

            border: none;
            margin: 0px;
            padding: 0px;
        }}



        QComboBox QAbstractItemView::item {{
            background-color: {t['surface']};

            color: {t['text2']};

            border: none;

            min-height: 30px;

            padding: 4px 8px;
            margin: 0px;
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {t['hover_select']};
            color: {t['text3']};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {t['hover_select']};
            color: {t['text3']};

            border: none;
        }}


        QScrollBar:vertical {{
            width: 0px;
            background: transparent;
        }}

        QScrollBar:horizontal {{
            height: 0px;
            background: transparent;
        }}
        """)

    # Change Theme

    def set_theme(self, is_dark):
        self._dark = is_dark
        self.apply_theme()

    def showPopup(self):
        t = self._get_colors()
        super().showPopup()
        view = self.view()

        view.setContentsMargins(0, 0, 0, 0)
        view.setStyleSheet(f"""
        background: {t['surface']};
        border: none;
        """)
