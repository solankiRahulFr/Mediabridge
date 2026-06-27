from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont

from core.app_state import get_state
from ui.themes.theme import THEMES


class StyledDialog(QDialog):
    def __init__(self, title, content_html, theme_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMaximumWidth(600)
        self._build(title, content_html, theme_name)

    def _get_colors(self, theme_name: str) -> dict[str, str]:
        state = get_state()
        if state.theme:
            return state.theme.colors
        return THEMES[theme_name]

    def _build(self, title, content_html, theme_name):
        t = self._get_colors(theme_name)
        self.setStyleSheet(
            f"QDialog {{ background: {t['bg2']};}}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(16)

        # title
        lbl = QLabel(title)
        tf = QFont(); tf.setPointSize(16); tf.setWeight(QFont.DemiBold)
        lbl.setFont(tf)
        lbl.setStyleSheet(f"color: {t['text']};")
        lay.addWidget(lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {t['border']};")
        lay.addWidget(sep)

        body = QLabel(content_html)
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        bf = QFont(); bf.setPointSize(10)
        body.setFont(bf)
        body.setStyleSheet(f"color: {t['text2']}; line-height: 1.6;")
        lay.addWidget(body)

        lay.addStretch()

        close_btn = QPushButton("Close")
        cf = QFont(); cf.setPointSize(10); cf.setWeight(QFont.Medium)
        close_btn.setFont(cf)
        close_btn.setFixedHeight(40)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(
            f"QPushButton {{ background: {t['accent']}; color: #fff; "
            f"border: none; border-radius: 8px; padding: 0 24px; }}"
            f"QPushButton:hover {{ background: {t['accent2']}; }}"
        )
        close_btn.clicked.connect(self.accept)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(close_btn)
        lay.addLayout(row)
