
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from core.app_state import get_state
from ui.themes.theme import THEMES


class ModeCard(QWidget):
    selected = Signal(str)

    def __init__(self, mode: dict, theme: str, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.theme_name = theme
        self._selected = False
        self._hovered = False
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._state = get_state()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()

    def _get_colors(self) -> dict[str, str]:
        if self._state.theme:
            return self._state.theme.colors
        return THEMES[self.theme_name]

    def _build(self):
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(24, 22, 24, 22)
        self.lay.setSpacing(10)

        # Icon row
        icon_row = QHBoxLayout()
        self.icon_lbl = QLabel(self.mode["icon"])
        font_icon = QFont(); font_icon.setPointSize(28)
        self.icon_lbl.setFont(font_icon)
        self.icon_lbl.setFixedSize(56, 56)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        icon_row.addWidget(self.icon_lbl)
        icon_row.addStretch()

        # selected badge
        self.badge = QLabel()
        badge_font = QFont(); badge_font.setPointSize(8); badge_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
        self.badge.setFont(badge_font)
        self.badge.setVisible(False)
        icon_row.addWidget(self.badge)
        self.lay.addLayout(icon_row)

        self.title_lbl = QLabel()
        title_font = QFont(); title_font.setPointSize(15); title_font.setWeight(QFont.DemiBold)
        self.title_lbl.setFont(title_font)
        self.lay.addWidget(self.title_lbl)

        self.sub_lbl = QLabel()
        sub_font = QFont(); sub_font.setPointSize(9)
        self.sub_lbl.setFont(sub_font)
        self.lay.addWidget(self.sub_lbl)

        self.desc_lbl = QLabel()
        self.desc_lbl.setWordWrap(True)
        desc_font = QFont(); desc_font.setPointSize(9)
        self.desc_lbl.setFont(desc_font)
        self.desc_lbl.setMinimumHeight(52)
        self.lay.addWidget(self.desc_lbl)

        # tags
        tag_row = QHBoxLayout(); tag_row.setSpacing(6)
        self.tag_widgets = []
        tags = self._state.t(f"modes.{self.mode['id']}.tags")
        tag_count = len(tags) if isinstance(tags, list) else 3
        for i in range(tag_count):
            t = QLabel()
            tf = QFont(); tf.setPointSize(8)
            t.setFont(tf)
            t.setContentsMargins(8, 3, 8, 3)
            self.tag_widgets.append(t)
            tag_row.addWidget(t)
        tag_row.addStretch()
        self.lay.addLayout(tag_row)

        self.retranslate_ui()
        self.apply_theme()
        self._state.lang.on_change(lambda _code: self.retranslate_ui())

    def set_selected(self, val: bool):
        self._selected = val
        self.badge.setVisible(val)
        self.apply_theme()
        self.update()

    def apply_theme(self):
        t = self._get_colors()
        if self._selected:
            bg = t["surface"]
            border_color = t["accent"]
        elif self._hovered:
            bg = t["card_hover"]
            border_color = t["border"]
        else:
            bg = t["surface"]
            border_color = t["border"]

        self.icon_lbl.setStyleSheet(f"color: {t['accent']};background: transparent; font-size: 28pt;")
        self.title_lbl.setStyleSheet(f"color: {t['text']};background: transparent; font-size: 15pt; font-weight: 600;")
        self.sub_lbl.setStyleSheet(f"color: {t['accent2']};background: transparent; font-size: 9pt;")
        self.desc_lbl.setStyleSheet(f"color: {t['text2']};background: transparent; font-size: 9pt;")
        self.badge.setStyleSheet(
            f"color: {t['accent2']}; background: {t['accent_glow']}; "
            f"border-radius: 4px; padding: 2px 8px;"
        )
        for tw in self.tag_widgets:
            tw.setStyleSheet(
                f"color: {t['text3']}; background: {t['surface2']}; "
                f"border: 1px solid {t['border']}; border-radius: 4px;"
            )

        self.setStyleSheet(
            f"ModeCard {{ background: {bg}; border: 2px solid {border_color}; "
            f"border-radius: 14px; }}"
        )

    def enterEvent(self, _):
        self._hovered = True
        self.apply_theme()

    def leaveEvent(self, _):
        self._hovered = False
        self.apply_theme()

    def mousePressEvent(self, _):
        self.selected.emit(self.mode["id"])

    def retranslate_ui(self):
        self.badge.setText(self._state.t("launch.selected"))
        self.title_lbl.setText(self._state.t(f"modes.{self.mode['id']}.label"))
        self.sub_lbl.setText(self._state.t(f"modes.{self.mode['id']}.sub"))
        self.desc_lbl.setText(self._state.t(f"modes.{self.mode['id']}.desc"))

        tags = self._state.t(f"modes.{self.mode['id']}.tags")
        if isinstance(tags, list):
            for i, widget in enumerate(self.tag_widgets):
                widget.setText(tags[i] if i < len(tags) else "")
        else:
            for i, widget in enumerate(self.tag_widgets):
                widget.setText(self._state.t(f"modes.{self.mode['id']}.tags.{i}"))
