from __future__ import annotations

import pathlib

from PySide6.QtWidgets import QWidget

_QSS_DIR = pathlib.Path(__file__).resolve().parent / "qss"

# Load order
_QSS_FILES = [
    "base.qss",
    "header_footer.qss",
    "buttons.qss",
    "inputs.qss",
    "panels.qss",
    "keyboard.qss",
]

# Colour palettes
THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg":            "#0D0F14",
        "bg2":           "#13161E",
        "surface":       "#1A1E2A",
        "surface2":      "#222738",
        "border":        "#2E3347",
        "accent":        "#4F8EF7",
        "accent2":       "#7B5EF8",
        "accent_glow":   "rgba(79,142,247,0.18)",
        "text":          "#EEF0F8",
        "text2":         "#8B90A8",
        "text3":         "#5C6080",
        "card_sel":      "#FF0000",
        "card_hover":    "#1B1F2E",
        "danger":        "#F75F5F",
        "success":       "#4FD1A5",
        "toggle_bg":     "#2A2E3D",
        "toggle_knob":   "#8B90A8",
        "hover_select":  "#d6f1ff",
        "selected_mode": "#2e8b57",
        "key_press":     "#5C5EAA",
        "key_hover":     "#3D3E6A",
    },
    "light": {
        "bg":            "#F0F2F8",
        "bg2":           "#E8EAF2",
        "surface":       "#FFFFFF",
        "surface2":      "#F5F6FC",
        "border":        "#D4D8EC",
        "accent":        "#3B6FD4",
        "accent2":       "#6344CC",
        "accent_glow":   "rgba(59,111,212,0.12)",
        "text":          "#1A1D2E",
        "text2":         "#5A5F7A",
        "text3":         "#9096B2",
        "card_sel":      "#FF0000",
        "card_hover":    "#F7F8FD",
        "danger":        "#D94040",
        "success":       "#2AA87A",
        "toggle_bg":     "#D4D8EC",
        "toggle_knob":   "#FFFFFF",
        "hover_select":  "#d6f1ff",
        "selected_mode": "#2e8b57",
        "key_press":     "#C5CAF5",
        "key_hover":     "#E8EAFF",

    },
}

# loading qss
def _load_qss_template() -> str:
    parts: list[str] = []
    for name in _QSS_FILES:
        path = _QSS_DIR / name
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


_QSS = _load_qss_template()


def apply_theme(widget: QWidget, is_dark: bool = True) -> None:
    t = THEMES["dark" if is_dark else "light"]
    widget.setStyleSheet(_QSS.format(**t))


class ThemeManager:
    def __init__(self, is_dark: bool = True) -> None:
        self._is_dark = is_dark

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    @property
    def colors(self) -> dict[str, str]:
        return THEMES["dark" if self._is_dark else "light"]

    def color(self, key: str) -> str:
        return self.colors.get(key, "#000000")

    def set_dark(self, is_dark: bool) -> None:
        self._is_dark = is_dark

    def toggle(self) -> bool:
        self._is_dark = not self._is_dark
        return self._is_dark

    def apply(self, widget: QWidget) -> None:
        apply_theme(widget, self._is_dark)

    def qss(self) -> str:
        return _QSS.format(**self.colors)
