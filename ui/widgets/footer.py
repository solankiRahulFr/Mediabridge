from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor


class Footer(QFrame):
    def __init__(
        self,
        buttons: list[tuple[str, str, callable]] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ConfigFooter")
        self.setFixedHeight(60)

        self._buttons: list[QPushButton] = []

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        lay.addWidget(self.status_label)
        lay.addStretch()

        for label, obj_name, slot in (buttons or []):
            btn = QPushButton(label)
            btn.setObjectName(obj_name)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(slot)
            lay.addWidget(btn)
            self._buttons.append(btn)

    # ── Public API ────────────────────────────────────────────────────────────
    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def button(self, index: int) -> QPushButton | None:
        if 0 <= index < len(self._buttons):
            return self._buttons[index]
        return None
