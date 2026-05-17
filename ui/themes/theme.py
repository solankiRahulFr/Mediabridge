"""
Single source of truth for:
  • THEMES dict        — all colour tokens for dark + light
  • STYLESHEET         — QSS template (uses .format(**tokens))
  • ThemeManager       — apply / switch themes on any QWidget
  • ThemeToggle        — animated pill toggle widget

Import pattern used throughout the project:
    from ui.themes.theme import ThemeManager, ThemeToggle, THEMES

ThemeManager is intentionally NOT a singleton — the AppState holds the shared
instance so ownership is explicit.

    # In main.py:
    from ui.themes.theme import ThemeManager
    from core.app_state import AppState
    tm = ThemeManager(AppState.instance().is_dark)
    AppState.instance().theme_manager = tm

    # In any widget:
    from core.app_state import AppState
    tm = AppState.instance().theme_manager
    tm.apply(self)
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRect, Qt,
)
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QWidget

# ─────────────────────────────────────────────────────────────────────────────
# Colour palettes
# ─────────────────────────────────────────────────────────────────────────────
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
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# QSS template — every colour token from THEMES is substituted at apply time
# ─────────────────────────────────────────────────────────────────────────────
_QSS = """
QStackedWidget {{background: {bg2};}}
QMainWindow {{ background: {bg}; }}
/* ── Root ─────────────────────────────────────────────────────────────────── */
QWidget {{
    background-color: {bg2};
    color: {text};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}
QMainWindow  {{
    background-color: {bg2};
    color: {text};
    font-family: "Segoe UI";
    font-size: 13px;
}}


/* ── Config window header ─────────────────────────────────────────────────── */
QWidget#Header {{
    background-color: {bg2};
    border-bottom: 1px solid {border};
}}
QLabel#HeaderTitle {{
    font-size: 17px;
    font-weight: 700;
    color: {text};
    letter-spacing: 0.3px;
}}

/* ── Nav rail ─────────────────────────────────────────────────────────────── */
QFrame#NavRail {{
    background-color: {bg};
    border-right: 1px solid {border};
}}
QPushButton#NavBtn {{
    background: transparent;
    color: {text2};
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#NavBtn:hover {{
    background-color: {surface};
    color: {text};
}}
QPushButton#NavBtn:checked {{
    background-color: {accent};
    color: #FFFFFF;
    font-weight: 700;
}}

/* ── Footer ───────────────────────────────────────────────────────────────── */
QFrame#ConfigFooter {{
    background-color: {bg};
    border-top: 1px solid {border};
}}
QLabel#StatusLabel {{
    color: {success};
    font-size: 12px;
}}

/* ── Section / card ───────────────────────────────────────────────────────── */
QFrame#Card {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 10px;
}}
QFrame#Card:hover {{
    border-color: {accent};
}}
QLabel#SectionTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {text};
    padding-bottom: 4px;
}}
QLabel#SectionDesc {{
    font-size: 12px;
    color: {text3};
}}
QLabel#FieldLabel {{
    font-size: 12px;
    font-weight: 600;
    color: {text2};
}}
QLabel#HintLabel {{
    font-size: 11px;
    color: {text3};
    font-style: italic;
}}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 7px;
    padding: 6px 10px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {accent};
    background-color: {surface};
}}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {text2};
}}
QComboBox QAbstractItemView {{
    background-color: {surface};
    border: 1px solid {border};
    selection-background-color: {accent};
    color: {text};
    border-radius: 7px;
}}

/* ── Checkboxes ───────────────────────────────────────────────────────────── */
QCheckBox {{
    color: {text};
    spacing: 10px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 2px solid {border};
    background-color: {surface2};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton#PrimaryBtn {{
    background-color: {accent};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 22px;
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#PrimaryBtn:hover  {{ background-color: {accent2}; }}

QPushButton#SecondaryBtn {{
    background-color: {surface2};
    color: {text};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#SecondaryBtn:hover {{ border-color: {accent}; color: {accent}; }}

QPushButton#CloseBtn {{
    background-color: transparent;
    color: {text2};
    border: none;
    border-radius: 18px;
    font-size: 15px;
}}
QPushButton#CloseBtn:hover {{ background-color: {danger}; color: #FFFFFF; }}

QPushButton#SmallBtn {{
    background-color: {surface2};
    color: {text2};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
}}
QPushButton#SmallBtn:hover {{ color: {accent}; border-color: {accent}; }}

QPushButton#DangerBtn {{
    background-color: transparent;
    color: {danger};
    border: 1px solid {danger};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
}}
QPushButton#DangerBtn:hover {{ background-color: {danger}; color: #FFFFFF; }}

/* ── Divider ──────────────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {border};
    background: {border};
    max-height: 1px;
    border: none;
}}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
    border: none;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {accent}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Mapping rows ─────────────────────────────────────────────────────────── */
QFrame#MappingRow {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 8px;
}}
QFrame#MappingRow:hover {{
    border-color: {accent};
    background-color: {card_hover};
}}
QLabel#SemanticKey {{
    font-weight: 700;
    color: {accent};
    font-size: 12px;
    font-family: "Fira Code", "Cascadia Code", "Consolas", monospace;
}}
QLabel#SemanticCategory {{
    font-size: 10px;
    color: {text3};
    font-family: "Fira Code", "Cascadia Code", "Consolas", monospace;
}}

/* ── Collapsible group header ─────────────────────────────────────────────── */
QPushButton#GroupHeader {{
    background-color: {surface2};
    color: {text2};
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 0 12px;
    font-weight: 700;
    font-size: 12px;
}}
QPushButton#GroupHeader:hover {{ color: {accent}; }}
/* ── Nav Tabs ───────────────────────────────────── */

QWidget#NavTabs {{
    background-color: {bg2};
    border: 1px solid {border};
}}

QPushButton#NavTabButton {{
    color: {text2};
    border: none;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#NavTabButton:hover {{
    background-color: {surface};
    color: {text};
}}

QPushButton#NavTabButton:checked {{
    background-color: {accent};
    color: white;
    font-weight: 700;
}}

QPushButton#NavTabButton:pressed {{
    background-color: {accent2};
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
def apply_theme(widget: QWidget, is_dark: bool = True) -> None:
    """Apply the compiled QSS for the chosen mode to *widget*."""
    t = THEMES["dark" if is_dark else "light"]
    widget.setStyleSheet(_QSS.format(**t))


# ─────────────────────────────────────────────────────────────────────────────
class ThemeManager:
    """
    Lightweight manager wrapping the THEMES dict.
    Passed by reference to panels/widgets — they call tm.apply(self).

    The shared instance lives on AppState; panels never create their own.
    """

    def __init__(self, is_dark: bool = True) -> None:
        self._is_dark = is_dark

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def is_dark(self) -> bool:
        return self._is_dark

    @property
    def colors(self) -> dict[str, str]:
        return THEMES["dark" if self._is_dark else "light"]

    def color(self, key: str) -> str:
        """Single token lookup, e.g. tm.color('accent')."""
        return self.colors.get(key, "#000000")

    # ── Switching ─────────────────────────────────────────────────────────────
    def set_dark(self, is_dark: bool) -> None:
        self._is_dark = is_dark

    def toggle(self) -> bool:
        self._is_dark = not self._is_dark
        return self._is_dark

    # ── Application ───────────────────────────────────────────────────────────
    def apply(self, widget: QWidget) -> None:
        """Apply the current palette QSS to *widget* and all its children."""
        apply_theme(widget, self._is_dark)

    def qss(self) -> str:
        """Return the raw compiled QSS string (useful for partial overrides)."""
        return _QSS.format(**self.colors)


# ─────────────────────────────────────────────────────────────────────────────
class ThemeToggle(QWidget):
    """
    Animated pill toggle — emits toggled(is_dark: bool).

    Drop-in for the header bar:
        self.theme_toggle = ThemeToggle(is_dark=True)
        self.theme_toggle.toggled.connect(self._on_theme_toggle)
        hdr_lay.addWidget(self.theme_toggle)
    """

    from PySide6.QtCore import Signal
    toggled = Signal(bool)

    def __init__(self, is_dark: bool = True,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_dark = is_dark
        self.setFixedSize(68, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._knob_x: float = 38.0 if is_dark else 6.0

        self._anim = QPropertyAnimation(self, b"knob_x", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    # ── Animated property ─────────────────────────────────────────────────────
    def _get_knob_x(self) -> float:
        return self._knob_x

    def _set_knob_x(self, v: float) -> None:
        self._knob_x = v
        self.update()

    knob_x = Property(float, _get_knob_x, _set_knob_x)

    # ── Interaction ───────────────────────────────────────────────────────────
    def mousePressEvent(self, _) -> None:  # noqa: ANN001
        self._is_dark = not self._is_dark
        target = 38.0 if self._is_dark else 6.0
        self._anim.setStartValue(self._knob_x)
        self._anim.setEndValue(target)
        self._anim.start()
        self.toggled.emit(self._is_dark)

    # ── Paint ─────────────────────────────────────────────────────────────────
    # def paintEvent(self, _) -> None:  # noqa: ANN001
    #     p = QPainter(self)
    #     p.setRenderHint(QPainter.Antialiasing)
    #     c = THEMES["dark" if self._is_dark else "light"]

    #     # Track
    #     p.setPen(Qt.NoPen)
    #     p.setBrush(QColor(c["toggle_bg"]))
    #     p.drawRoundedRect(0, 4, 68, 24, 12, 12)

    #     # Icon labels
    #     p.setPen(QColor(c["text3"]))
    #     p.setFont(QFont("Segoe UI Emoji", 10))
    #     p.drawText(QRect(5, 6, 20, 20), Qt.AlignCenter, "☀")
    #     p.drawText(QRect(42, 6, 20, 20), Qt.AlignCenter, "🌙")

    #     # Knob
    #     p.setPen(Qt.NoPen)
    #     p.setBrush(QColor(c["accent"]))
    #     p.drawEllipse(int(self._knob_x), 6, 20, 20)