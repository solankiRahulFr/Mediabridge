"""
    kb = VirtualKeyboard(parent=central_widget)
    kb.attach(my_line_edit)

    # Manual control
    kb.set_enabled(True)   # enable / disable
"""

from PySide6.QtCore import (
    Qt, Signal, QEvent, QObject
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout,
    QPushButton, QSizePolicy, QLineEdit, QTextEdit,
    QFrame, QLabel,
)
from core.app_state import get_state


def _screen_size():
    app = QGuiApplication.instance()
    if app:
        geo = app.primaryScreen().availableGeometry()
        return geo.width(), geo.height()
    return 1920, 1080  # fallback


_cached_metrics = None

def _kb_metrics():
    global _cached_metrics
    if _cached_metrics is not None:
        return _cached_metrics

    sw, sh = _screen_size()

    # Internal overhead: toolbar(24) + divider(2) + margins(16)
    #                  + root spacing(10) + row gaps(16) = 68
    _OVERHEAD = 68

    # Budget 35 % of screen height for the keyboard, derive key height
    budget = int(sh * 0.35)
    key_h  = max(22, min(44, (budget - _OVERHEAD) // 5))
    panel_h = 5 * key_h + _OVERHEAD

    # Horizontal scale [0..1] mapped from screen width [800..1280]
    ht = max(0.0, min(1.0, (sw - 800) / 480))

    _cached_metrics = {
        "panel_h":   panel_h,
        "key_h":     key_h,
        "key_min_w": int(20 + ht * 16),     # 20 .. 36
        "special_w": int(32 + ht * 30),     # 32 .. 62
        "enter_w":   int(44 + ht * 38),     # 44 .. 82
        "space_w":   int(100 + ht * 150),   # 100 .. 250
        "font_size": max(11, int(11 + ht * 7)),  # 11 .. 18
        "border_r":  max(4, int(4 + ht * 3)),    # 4 .. 7
    }
    return _cached_metrics


# LAYOUTS
def _row(keys):
    out = []
    for k in keys:
        if isinstance(k, tuple):
            out.append(k)
        else:
            out.append((k, k.lower(), k.upper()))
    return out

def _sym_row(chars):
    return [(c, c, c) for c in chars]

LAYOUTS = {
    "EN 🇬🇧": [
        _row("1234567890"),
        _row("QWERTYUIOP"),
        _row("ASDFGHJKL"),
        [("⇧","⇧","⇧")] + _row("ZXCVBNM") + [("⌫","⌫","⌫")],
        # added ?123 toggle here; ⇪ still available
        [("⇪","⇪","⇪"), ("?123","?123","?123"), ("␣","␣","␣"), ("⏎","⏎","⏎")],
    ],
    "SYM": [
        _sym_row("!@#$%^&*()"),
        _sym_row("-_=+[]{}\\"),
        _sym_row("/|<>~`€£¥"),
        _sym_row(";:'\",.?!") + [("⌫","⌫","⌫")],
        [("ABC","ABC","ABC"), ("␣","␣","␣"),
         ("√","√","√"), ("π","π","π"), ("÷","÷","÷"),
         ("×","×","×"), ("°","°","°"), ("⏎","⏎","⏎")],
    ],
}

ACCENTS = {
    "EN 🇬🇧": ["à","â","ä","é","è","ê","ë","î","ï","ô","ù","û","ü","ç","œ","æ",
                "À","Â","Ä","É","È","Ê","Ë","Î","Ï","Ô","Ù","Û","Ü","Ç","Œ","Æ"],
}

SPECIAL_KEYS = {"⌫", "⏎", "⇧", "⇪", "␣"}


# KEY BUTTON
class KeyButton(QPushButton):

    @staticmethod
    def metric(name):
        return _kb_metrics()[name]

    @staticmethod
    def is_compact():
        w, _ = _screen_size()
        return w < 1280

    def __init__(self, label, value_normal, value_shift,
                 special=False, parent=None):
        super().__init__(label, parent)
        self.value_normal = value_normal
        self.value_shift  = value_shift
        self.is_special   = special
        m = _kb_metrics()
        self.setFixedHeight(m["key_h"])
        self.setMinimumWidth(m["key_min_w"])
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setObjectName("KBSpecial" if special else "KBKey")

    def current_value(self, shifted: bool) -> str:
        return self.value_shift if shifted else self.value_normal

    def is_alpha_key(self) -> bool:
        return (
            not self.is_special
            and len(self.value_normal) == 1
            and self.value_normal.isalpha()
        )

    def sync_label(self, shifted: bool) -> None:
        if self.is_alpha_key():
            self.setText(self.current_value(shifted))


# ACCENT PANEL
class AccentPanel(QFrame):
    char_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._grid     = QGridLayout(self)
        self._grid.setSpacing(4)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._buttons  = []
        self.setObjectName("AccentPanel")

    def populate(self, chars, keyboard, compact=False):
        for b in self._buttons:
            b.deleteLater()
        self._buttons.clear()
        self._kb_ref = keyboard

        cols = 8
        btn_sz = 30 if compact else 38
        for i, ch in enumerate(chars):
            btn = QPushButton(ch)
            btn.setFixedSize(btn_sz, btn_sz)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setObjectName("KBKey")
            def _on_accent_click(checked=False, c=ch):
                self.char_clicked.emit(c)
                self._kb_ref._accent_open = False
                self.hide()
            btn.clicked.connect(_on_accent_click)
            self._grid.addWidget(btn, i // cols, i % cols)
            self._buttons.append(btn)


# INPUT TAP FILTER
class _InputTapFilter(QObject):

    def __init__(self, keyboard, widget, parent=None):
        super().__init__(parent)
        self._kb     = keyboard
        self._widget = widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and self._kb._enabled:
            self._kb._open_for(self._widget)
            return True          # consume — don't focus the underlying input
        return False


# VIRTUAL KEYBOARD WIDGET
class VirtualKeyboard(QWidget):
    """

    kb = VirtualKeyboard(parent=container)
    kb.attach(my_line_edit)

    kb.set_enabled(on)   — global on / off gate
    kb.is_enabled()      — query
    kb.close_kb()        — dismiss the overlay (also writes text back)
    """

    key_pressed  = Signal(str)
    ANIM_MS      = 250

    # ── init ──────────────────────────────────────────────────────────────────

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setFocusPolicy(Qt.NoFocus)

        self._language     = list(LAYOUTS.keys())[0]
        self._shifted      = False
        self._caps         = False
        self._targets      = []
        self._last_target  = None
        self._accent_open  = False
        self._enabled      = True

        self._state = get_state()

        self._accent_panel = AccentPanel()
        self._accent_panel.char_clicked.connect(self._emit_char)

        self._key_buttons: list[KeyButton] = []

        self._build_ui()
        self._build_keyboard()

        # Track parent resizes so the overlay always fills the parent
        if parent:
            parent.installEventFilter(self)

        self._state.subscribe("is_dark", self._on_app_theme_changed)
        self._apply_theme()

    # ── Public API ────────────────────────────────────────────────────────────

    def attach(self, widget, window=None):
        filt = _InputTapFilter(self, widget, parent=widget)
        widget.installEventFilter(filt)
        self._targets.append((widget, filt))

    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)
        if not self._enabled:
            self.close_kb()

    def is_enabled(self) -> bool:
        return self._enabled

    def close_kb(self):
        if self._last_target is not None and self.isVisible():
            text = self._input.text()
            if isinstance(self._last_target, QLineEdit):
                self._last_target.setText(text)
            elif isinstance(self._last_target, QTextEdit):
                self._last_target.setPlainText(text)
        self._accent_panel.hide()
        self._accent_open = False
        self.hide()

    # ── Open for a specific widget ────────────────────────────────────────────

    def _open_for(self, widget):
        if not self._enabled:
            return
        self._last_target = widget

        # Copy current text into overlay input
        if isinstance(widget, QLineEdit):
            self._input.setText(widget.text())
            label = widget.placeholderText() or ""
        elif isinstance(widget, QTextEdit):
            self._input.setText(widget.toPlainText())
            label = ""
        else:
            self._input.clear()
            label = ""
        # self._field_label.setText(label)

        # Fill parent
        self._resize_to_parent()
        self.raise_()
        self.show()

    # ── Geometry helpers ──────────────────────────────────────────────────────

    def _resize_to_parent(self):
        p = self.parent()
        if p:
            self.setGeometry(0, 0, p.width(), p.height())

    def showEvent(self, event):
        super().showEvent(event)
        self._resize_to_parent()

    def eventFilter(self, obj, event):
        """Track parent resize so overlay stays full-size while visible."""
        if obj == self.parent() and event.type() == QEvent.Resize:
            if self.isVisible():
                size = event.size()
                self.setGeometry(0, 0, size.width(), size.height())
        return super().eventFilter(obj, event)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        m = _kb_metrics()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Backdrop (tap to close) ───────────────────────────────────────────
        self._backdrop = QWidget()
        self._backdrop.setObjectName("VKBBackdrop")
        self._backdrop.mousePressEvent = lambda e: self.close_kb()
        root.addWidget(self._backdrop, 1)       # stretches to fill

        # ── Panel ─────────────────────────────────────────────────────────────
        self._panel = QFrame()
        self._panel.setObjectName("VirtualKeyboard")
        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(10, 8, 10, 10)
        # panel_lay.setSpacing(6)

        # Header: label + accent + close
        hdr = QHBoxLayout()

        # self._field_label = QLabel("")
        # self._field_label.setObjectName("VKBLabel")
        # hdr.addWidget(self._field_label)
        
        
        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("KBCloseBtn")
        self._close_btn.setFixedSize(34, 34)
        self._close_btn.setFocusPolicy(Qt.NoFocus)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self.close_kb)
        hdr.addWidget(self._close_btn)
        hdr.addStretch()


        self._accent_btn = QPushButton("Á")
        self._accent_btn.setObjectName("KBAccentBtn")
        self._accent_btn.setFixedSize(34, 34)
        self._accent_btn.setFocusPolicy(Qt.NoFocus)
        self._accent_btn.setCursor(Qt.PointingHandCursor)
        self._accent_btn.setToolTip("Show accent characters")
        self._accent_btn.clicked.connect(self._toggle_accent_panel)
        hdr.addWidget(self._accent_btn)
       



        panel_lay.addLayout(hdr)

        # Input field + accept button
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setObjectName("VKBInput")
        self._input.setMinimumHeight(m["key_h"] + 8)
        self._input.setFocusPolicy(Qt.NoFocus)
        input_row.addWidget(self._input)

        self._accept_btn = QPushButton("✓")
        self._accept_btn.setObjectName("KBAcceptBtn")
        self._accept_btn.setFixedSize(m["key_h"] + 8, m["key_h"] - 10)
        self._accept_btn.setFocusPolicy(Qt.NoFocus)
        self._accept_btn.setCursor(Qt.PointingHandCursor)
        self._accept_btn.clicked.connect(self.close_kb)
        input_row.addWidget(self._accept_btn)

        panel_lay.addLayout(input_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        panel_lay.addWidget(divider)

        # Key area
        self._key_area = QWidget()
        self._key_rows = QVBoxLayout(self._key_area)
        self._key_rows.setSpacing(4)
        self._key_rows.setContentsMargins(0, 0, 0, 0)
        panel_lay.addWidget(self._key_area)

        root.addWidget(self._panel)

    def _build_keyboard(self):
        for btn in self._key_buttons:
            btn.deleteLater()
        self._key_buttons.clear()

        while self._key_rows.count():
            item = self._key_rows.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        m = _kb_metrics()
        layout = LAYOUTS[self._language]
        LAST_ROW_STRETCH = {
        "⇪":    2,
        "?123": 2,
        "␣":    6,
        "⏎":    2,
        # SYM layer bottom row
        "ABC":  2,
        "√":    1, "π": 1, "÷": 1, "×": 1, "°": 1,
    }
        for row_idx, row_def in enumerate(layout):
            is_last = (row_idx == len(layout) - 1)
            row_w = QWidget()
            row_l = QHBoxLayout(row_w)
            row_l.setSpacing(4)
            row_l.setContentsMargins(0, 0, 0, 0)

            for (label, val_n, val_s) in row_def:
                special = label in SPECIAL_KEYS
                btn = KeyButton(label, val_n, val_s, special=special)

                if label == "␣":
                    btn.setMinimumWidth(m["space_w"])
                elif label in ("⇧", "⇪", "⌫"):
                    btn.setMinimumWidth(m["special_w"])
                elif label == "⏎":
                    btn.setMinimumWidth(m["enter_w"])

                btn.clicked.connect(lambda _, b=btn: self._on_key(b))

                
                if is_last and label in LAST_ROW_STRETCH:
                    row_l.addWidget(btn, LAST_ROW_STRETCH[label])  # <-- stretch factor
                else:
                    row_l.addWidget(btn)  
                self._key_buttons.append(btn)

            self._key_rows.addWidget(row_w)

        self._update_key_labels()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _apply_theme(self):
        if not self._state.theme:
            return
        tm = self._state.theme
        tm.apply(self)
        tm.apply(self._accent_panel)
        self._update_shift_visual()

    def _on_app_theme_changed(self, is_dark: bool):
        if self._state.theme:
            self._state.theme.set_dark(is_dark)
        self._apply_theme()

    # ── Key logic ─────────────────────────────────────────────────────────────

    def _on_key(self, btn: KeyButton):
        label = btn.text()
        val   = btn.current_value(self._shifted or self._caps)

        if   label == "⌫": self._emit_char("\x08")
        elif label == "⏎": self._emit_char("\n")
        elif label == "␣": self._emit_char(" ")
        elif label == "⇧":
            self._shifted = not self._shifted
            self._update_shift_visual()
        elif label == "⇪":
            self._caps = not self._caps
            self._update_shift_visual()
        elif label == "?123":
            self._language = "SYM"
            self._build_keyboard()
        elif label == "ABC":
            self._language = list(LAYOUTS.keys())[0]
            self._build_keyboard()
        else:
            self._emit_char(val)
            if self._shifted:
                self._shifted = False
                self._update_shift_visual()

    def _emit_char(self, ch: str):
        self.key_pressed.emit(ch)
        if ch == "\x08":
            self._input.backspace()
        else:
            self._input.insert(ch)

    def _update_key_labels(self):
        shifted = self._shifted or self._caps
        for btn in self._key_buttons:
            btn.sync_label(shifted)

    def _update_shift_visual(self):
        self._update_key_labels()

        if not self._state.theme:
            return

        tm     = self._state.theme
        colors = tm.colors

        active = self._shifted or self._caps
        bg     = colors["accent"]  if active else colors["surface2"]
        hover  = colors["accent2"] if active else colors["surface"]
        m      = _kb_metrics()
        fs     = m["font_size"]
        r      = m["border_r"]

        for btn in self._key_buttons:
            if btn.text() in ("⇧", "⇪"):
                if active:
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {bg}; color: white;
                            border: 1px solid {colors['border']};
                            border-radius: {r}px;
                            font-size: {fs}px; padding: 2px 4px;
                        }}
                        QPushButton:hover {{ background: {hover}; }}
                    """)
                else:
                    btn.setStyleSheet("")

    # ── Accent panel ──────────────────────────────────────────────────────────

    def _toggle_accent_panel(self):
        if self._accent_panel.isVisible():
            self._accent_open = False
            self._accent_panel.hide()
            return
        chars = ACCENTS.get(self._language, [])
        if not chars:
            return
        self._accent_panel.populate(chars, self, compact=KeyButton.is_compact())
        self._accent_panel.adjustSize()
        btn_global = self._accent_btn.mapToGlobal(self._accent_btn.rect().topLeft())
        size = self._accent_panel.sizeHint()
        self._accent_panel.move(btn_global.x(), btn_global.y() - size.height() - 6)
        self._accent_open = True
        self._accent_panel.show()
        self._accent_panel.raise_()

    def _on_lang_changed(self, lang):
        self._language = lang
        self._build_keyboard()
        self._accent_panel.hide()
