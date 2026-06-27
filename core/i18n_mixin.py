from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class I18nMixin:

    def __init__(self, *args, **kwargs):
        self._i18n_text_targets: list[QWidget] = []
        self._i18n_placeholder_targets: list[QWidget] = []
        super().__init__(*args, **kwargs)

    def _bind_text(self, widget: QWidget, key: str) -> None:
        widget.setProperty("i18n_key", key)
        widget.setText(self._state.lang.t(key))
        self._i18n_text_targets.append(widget)

    def _bind_placeholder(self, widget: QWidget, key: str) -> None:
        widget.setProperty("i18n_placeholder_key", key)
        widget.setPlaceholderText(self._state.lang.t(key))
        self._i18n_placeholder_targets.append(widget)

    def _do_retranslate(self) -> None:
        # Update text widgets
        for widget in self._i18n_text_targets:
            key = widget.property("i18n_key")
            if key:
                widget.setText(self._state.lang.t(key))

        # Update placeholder widgets
        for widget in self._i18n_placeholder_targets:
            key = widget.property("i18n_placeholder_key")
            if key:
                widget.setPlaceholderText(self._state.lang.t(key))

    def retranslate_ui(self) -> None:
        self._do_retranslate()
