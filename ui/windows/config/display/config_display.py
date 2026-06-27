
from __future__ import annotations
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QFileDialog, QFrame, QScrollArea, QButtonGroup,
    QListWidget, QListWidgetItem,
)

from core.app_state import get_state
from core.theme import ThemeManager
from ui.themes.theme import THEMES
from ui.widgets.header import Header
from core.configio import ConfigIO
from core.i18n_mixin import I18nMixin
from ...display.display_controller import DisplayController
from .display_data import DisplayModeConfig

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _divider() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.HLine); f.setFrameShadow(QFrame.Sunken)
    return f

def _title(text: str) -> QLabel:
    l = QLabel(text); l.setObjectName("SectionTitle"); return l

def _label(text: str) -> QLabel:
    l = QLabel(text); l.setObjectName("FieldLabel"); return l

def _hint(text: str) -> QLabel:
    l = QLabel(text); l.setObjectName("HintLabel"); return l

def _card() -> QFrame:
    f = QFrame(); f.setObjectName("Card"); return f


# ── Config panel ──────────────────────────────────────────────────────────────
class DisplayConfigPanel(I18nMixin, QWidget):
    def __init__(self, controller: DisplayController,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ctrl = controller
        self._state = get_state()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body_widget = QWidget()
        body = QVBoxLayout(body_widget)
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(16)

        self._page_title = _title("")
        self._bind_text(self._page_title, "config_display_mode.title")
        body.addWidget(self._page_title)
        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

        # ── Window ────────────────────────────────────────────────────────────
        self._window_title = _title("")
        self._bind_text(self._window_title, "config_display_mode.config.window.title")
        body.addWidget(self._window_title)
        win = _card()
        wl = QVBoxLayout(win); wl.setSpacing(10)

        self._chk_fs = QCheckBox("")
        self._bind_text(self._chk_fs, "config_display_mode.config.window.fullscreen")
        self._chk_fs.setChecked(True)
        self._chk_ctrl = QCheckBox("")
        self._bind_text(self._chk_ctrl, "config_display_mode.config.window.control")
        wl.addWidget(self._chk_fs)
        wl.addWidget(self._chk_ctrl)

        hr = QHBoxLayout()
        self._screen_label = _label("")
        self._bind_text(self._screen_label, "config_display_mode.config.window.screen")
        hr.addWidget(self._screen_label)
        self._cmb_screen = QComboBox()
        self._populate_screens(self._cmb_screen, default=1)
        self._cmb_screen.setMinimumWidth(220)
        hr.addWidget(self._cmb_screen); hr.addStretch()
        wl.addLayout(hr)
        body.addWidget(win)

        # ── Exit / escape hatch ───────────────────────────────────────────────
        body.addWidget(_divider())
        self._exit_title = _title("")
        self._bind_text(self._exit_title, "config_display_mode.config.exit.title")
        body.addWidget(self._exit_title)
        exit_card = _card()
        el = QVBoxLayout(exit_card); el.setSpacing(10)
        el.setSpacing(14)
        hk = QHBoxLayout()
        self._hotkey_label = _label("")
        self._bind_text(self._hotkey_label, "config_display_mode.config.exit.hotkey")
        hk.addWidget(self._hotkey_label)
        self._edit_hotkey = QLineEdit("Ctrl+Shift+Q")
        self._edit_hotkey.setFixedWidth(160)
        hk.addWidget(self._edit_hotkey); hk.addStretch()
        el.addLayout(hk)
        self._exit_hint = _hint("")
        self._bind_text(self._exit_hint, "config_display_mode.config.exit.info")
        el.addWidget(self._exit_hint)

        body.addWidget(exit_card)

        # ── Content type tabs ─────────────────────────────────────────────────
        body.addWidget(_divider())
        self._content_title = _title("")
        self._bind_text(self._content_title, "config_display_mode.config.content.title")
        body.addWidget(self._content_title)

        tab_row = QHBoxLayout(); tab_row.setSpacing(0)
        self._type_group = QButtonGroup(self)
        for ct, key in [
            ("url", "config_display_mode.config.content.url.label"),
            ("image", "config_display_mode.config.content.image.label"),
            ("pdf", "config_display_mode.config.content.pdf.label"),
            ("video", "config_display_mode.config.content.video.label"),
            ("stream", "config_display_mode.config.content.stream.label"),
        ]:
            btn = QPushButton("")
            self._bind_text(btn, key)
            btn.setCheckable(True)
            btn.setObjectName("NavTabButton")
            btn.setFixedHeight(34)
            btn.setProperty("ctype", ct)
            self._type_group.addButton(btn)
            tab_row.addWidget(btn)
        tab_row.addStretch()
        body.addLayout(tab_row)
        self._type_group.buttons()[0].setChecked(True)
        self._type_group.buttonClicked.connect(self._on_type_tab)

        # ── URL ───────────────────────────────────────────────────────────────
        self._url_card = _card()
        ul = QVBoxLayout(self._url_card)
        self._url_title = _label("")
        self._bind_text(self._url_title, "config_display_mode.config.content.url.title")
        ul.addWidget(self._url_title)
        self._edit_url = QLineEdit("https://www.google.com")
        ul.addWidget(self._edit_url)
        hr2 = QHBoxLayout()
        self._refresh_label = _label("")
        self._bind_text(self._refresh_label, "config_display_mode.config.content.url.refresh")
        hr2.addWidget(self._refresh_label)
        self._spin_refresh = QDoubleSpinBox()
        self._spin_refresh.setRange(0, 1440); self._spin_refresh.setDecimals(1)
        self._spin_refresh.setFixedWidth(80)
        hr2.addWidget(self._spin_refresh); hr2.addStretch()
        ul.addLayout(hr2)
        body.addWidget(self._url_card)

        # ── Image ─────────────────────────────────────────────────────────────
        self._img_card = _card()
        il = QVBoxLayout(self._img_card)
        self._img_title = _label("")
        self._bind_text(self._img_title, "config_display_mode.config.content.image.title")
        il.addWidget(self._img_title)
        self._img_list = QListWidget(); self._img_list.setFixedHeight(90)
        il.addWidget(self._img_list)
        il.setSpacing(14)
        br = QHBoxLayout()
        self._btn_add = QPushButton("")
        self._bind_text(self._btn_add, "config_display_mode.config.content.image.add")
        self._btn_add.setObjectName("SmallBtnImp")
        self._btn_add.clicked.connect(self._add_images)
        self._btn_clr = QPushButton("")
        self._bind_text(self._btn_clr, "config_display_mode.config.content.image.clear")
        self._btn_clr.setObjectName("DangerBtn")
        self._btn_clr.clicked.connect(self._img_list.clear)
        br.addWidget(self._btn_add); br.addWidget(self._btn_clr); br.addStretch()
        il.addLayout(br)
        il.setSpacing(14)
        hr3 = QHBoxLayout()
        self._img_interval_label = _label("")
        self._bind_text(self._img_interval_label, "config_display_mode.config.content.image.interval")
        hr3.addWidget(self._img_interval_label)
        self._spin_img_int = QSpinBox()
        self._spin_img_int.setRange(1, 3600); self._spin_img_int.setValue(10)
        self._spin_img_int.setFixedWidth(80)
        hr3.addWidget(self._spin_img_int); hr3.addStretch()
        il.addLayout(hr3)
        il.setSpacing(14)
        self._chk_ss = QCheckBox("")
        self._bind_text(self._chk_ss, "config_display_mode.config.content.image.screensaver")
        il.addWidget(self._chk_ss)
        hr4 = QHBoxLayout()
        self._fit_label = _label("")
        self._bind_text(self._fit_label, "config_display_mode.config.content.image.fit")
        hr4.addWidget(self._fit_label)
        self._cmb_fit = QComboBox()
        self._cmb_fit.addItems(["contain", "fill", "stretch"])
        hr4.addWidget(self._cmb_fit); hr4.addStretch()
        il.addLayout(hr4)
        body.addWidget(self._img_card)
        self._img_card.hide()

        # ── PDF ───────────────────────────────────────────────────────────────
        self._pdf_card = _card()
        pl = QVBoxLayout(self._pdf_card)
        self._pdf_title = _label("")
        self._bind_text(self._pdf_title, "config_display_mode.config.content.pdf.title")
        pl.addWidget(self._pdf_title)
        ph = QHBoxLayout()
        self._edit_pdf = QLineEdit("")
        self._bind_placeholder(self._edit_pdf, "config_display_mode.config.content.pdf.placeholder")
        self._btn_pdf = QPushButton("")
        self._bind_text(self._btn_pdf, "config_display_mode.config.content.pdf.browse")
        self._btn_pdf.setObjectName("SecondaryBtn")
        self._btn_pdf.clicked.connect(self._browse_pdf)
        ph.addWidget(self._edit_pdf); ph.addWidget(self._btn_pdf)
        pl.addLayout(ph)
        hr5 = QHBoxLayout()
        self._pdf_interval_label = _label("")
        self._bind_text(self._pdf_interval_label, "config_display_mode.config.content.pdf.interval")
        hr5.addWidget(self._pdf_interval_label)
        self._spin_pdf_int = QSpinBox()
        self._spin_pdf_int.setRange(1, 600); self._spin_pdf_int.setValue(5)
        self._spin_pdf_int.setFixedWidth(80)
        hr5.addWidget(self._spin_pdf_int); hr5.addStretch()
        pl.addLayout(hr5)
        self._chk_pdf_loop = QCheckBox("")
        self._bind_text(self._chk_pdf_loop, "config_display_mode.config.content.pdf.loop")
        self._chk_pdf_loop.setChecked(True)
        pl.addWidget(self._chk_pdf_loop)
        body.addWidget(self._pdf_card)
        self._pdf_card.hide()

        # ── Video (local / direct URL) ────────────────────────────────────────
        self._vid_card = _card()
        vl = QVBoxLayout(self._vid_card)
        self._vid_title = _label("")
        self._bind_text(self._vid_title, "config_display_mode.config.content.video.title")
        vl.addWidget(self._vid_title)
        vh = QHBoxLayout()
        self._edit_video = QLineEdit("")
        self._bind_placeholder(self._edit_video, "config_display_mode.config.content.video.placeholder")
        self._btn_vid = QPushButton("")
        self._bind_text(self._btn_vid, "config_display_mode.config.content.video.browse")
        self._btn_vid.setObjectName("SecondaryBtn")
        self._btn_vid.clicked.connect(self._browse_video)
        vh.addWidget(self._edit_video); vh.addWidget(self._btn_vid)
        vl.addLayout(vh)
        self._video_hint = _hint("")
        self._bind_text(self._video_hint, "config_display_mode.config.content.video.hint")
        vl.addWidget(self._video_hint)
        self._chk_vid_loop = QCheckBox("")
        self._bind_text(self._chk_vid_loop, "config_display_mode.config.content.video.loop")
        self._chk_vid_loop.setChecked(True)
        self._chk_vid_muted = QCheckBox("")
        self._bind_text(self._chk_vid_muted, "config_display_mode.config.content.video.muted")
        vl.addWidget(self._chk_vid_loop); vl.addWidget(self._chk_vid_muted)
        body.addWidget(self._vid_card)
        self._vid_card.hide()

        # ── Stream (YouTube / Vimeo / embed) ──────────────────────────────────
        self._stream_card = _card()
        sl = QVBoxLayout(self._stream_card)
        self._stream_title = _label("")
        self._bind_text(self._stream_title, "config_display_mode.config.content.stream.title")
        sl.addWidget(self._stream_title)
        self._edit_stream = QLineEdit("")
        self._bind_placeholder(self._edit_stream, "config_display_mode.config.content.stream.placeholder")
        sl.addWidget(self._edit_stream)
        self._chk_s_autoplay = QCheckBox("")
        self._bind_text(self._chk_s_autoplay, "config_display_mode.config.content.stream.autoplay")
        self._chk_s_autoplay.setChecked(True)
        self._chk_s_loop = QCheckBox("")
        self._bind_text(self._chk_s_loop, "config_display_mode.config.content.stream.loop")
        self._chk_s_loop.setChecked(True)
        self._chk_s_muted = QCheckBox("")
        self._bind_text(self._chk_s_muted, "config_display_mode.config.content.stream.muted")
        self._chk_s_muted.setChecked(True)
        sl.addWidget(self._chk_s_autoplay)
        sl.addWidget(self._chk_s_loop)
        sl.addWidget(self._chk_s_muted)
        body.addWidget(self._stream_card)
        self._stream_card.hide()

        body.addStretch()

        # ── Footer ────────────────────────────────────────────────────────────
        footer = QFrame(); footer.setObjectName("ConfigFooter"); footer.setFixedHeight(60)
        fl = QHBoxLayout(footer); fl.setContentsMargins(16, 0, 16, 0)
        self._status = QLabel(""); self._status.setObjectName("StatusLabel")
        fl.addWidget(self._status); fl.addStretch()

        self._btn_stop = QPushButton("")
        self._bind_text(self._btn_stop, "config_display_mode.stop")
        self._btn_stop.setObjectName("SecondaryBtn")
        self._btn_stop.clicked.connect(self._stop)
        fl.addWidget(self._btn_stop)

        self._btn_launch = QPushButton("")
        self._bind_text(self._btn_launch, "config_display_mode.launch")
        self._btn_launch.setObjectName("PrimaryBtn")
        self._btn_launch.clicked.connect(self._launch)
        fl.addWidget(self._btn_launch)

        root.addWidget(footer)
        # Set cursor for existing checkboxes
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setCursor(Qt.PointingHandCursor)
        for btn in self.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
        for dropdown in self.findChildren(QComboBox):
            dropdown.setCursor(Qt.PointingHandCursor)

    # ── Slots ──────────────────────────────────────────────────────────────────
    def _on_type_tab(self, btn: QPushButton) -> None:
        ct = btn.property("ctype")
        self._url_card.setVisible(ct == "url")
        self._img_card.setVisible(ct == "image")
        self._pdf_card.setVisible(ct == "pdf")
        self._vid_card.setVisible(ct == "video")
        self._stream_card.setVisible(ct == "stream")

    def _add_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        for f in files:
            self._img_list.addItem(QListWidgetItem(f))

    def _browse_pdf(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF (*.pdf)")
        if f: self._edit_pdf.setText(f)

    def _browse_video(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Select video", "",
            "Video (*.mp4 *.mkv *.avi *.mov *.webm *.m4v)"
        )
        if f: self._edit_video.setText(f)

    def _populate_screens(self, combo: QComboBox, default: int = 0) -> None:
        combo.clear()
        screens = QGuiApplication.screens()
        for i, scr in enumerate(screens):
            geo = scr.geometry()
            label = f"Screen {i}: {scr.name()}  ({geo.width()}×{geo.height()})"
            combo.addItem(label, i)
        idx = min(default, len(screens) - 1) if screens else 0
        combo.setCurrentIndex(idx)

    def _build_config(self) -> DisplayModeConfig:
        btn = self._type_group.checkedButton()
        ct  = btn.property("ctype") if btn else "url"
        imgs = [self._img_list.item(i).text() for i in range(self._img_list.count())]
        return DisplayModeConfig(
            fullscreen           = self._chk_fs.isChecked(),
            controllable         = self._chk_ctrl.isChecked(),
            target_screen_index  = self._cmb_screen.currentData(),
            content_type         = ct,
            # exit
            exit_hotkey          = self._edit_hotkey.text().strip() or "Ctrl+Shift+Q",
            # show_exit_badge      = self._chk_badge.isChecked(),
            # exit_badge_position  = self._cmb_badge_pos.currentText(),
            # system_tray_exit     = self._chk_tray.isChecked(),
            # url
            url                  = self._edit_url.text().strip() or "https://example.com",
            url_refresh_minutes  = self._spin_refresh.value(),
            # image
            image_paths          = imgs,
            image_interval_seconds = self._spin_img_int.value(),
            image_screensaver_mode = self._chk_ss.isChecked(),
            image_fit            = self._cmb_fit.currentText(),
            # pdf
            pdf_path             = self._edit_pdf.text().strip(),
            pdf_page_interval_seconds = self._spin_pdf_int.value(),
            pdf_loop             = self._chk_pdf_loop.isChecked(),
            # video
            video_path           = self._edit_video.text().strip(),
            video_loop           = self._chk_vid_loop.isChecked(),
            video_muted          = self._chk_vid_muted.isChecked(),
            # stream
            stream_url           = self._edit_stream.text().strip(),
            stream_autoplay      = self._chk_s_autoplay.isChecked(),
            stream_loop          = self._chk_s_loop.isChecked(),
            stream_muted         = self._chk_s_muted.isChecked(),
        )

    def _launch(self) -> None:
        cfg = self._build_config()
        self._ctrl.update_config(cfg)
        self._ctrl.launch()
        self._status.setText("● Display active")
        # Listen for the display's own close signal to update status
        if self._ctrl._window:
            self._ctrl._window.closed.connect(
                lambda: self._status.setText("■ Stopped (closed from display)")
            )

    def _stop(self) -> None:
        self._ctrl.close()
        self._status.setText("■ Stopped")

class ConfigWindowDisplay(I18nMixin, QWidget):
    config_saved = Signal(dict)
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None, is_dark: bool = True):
        super().__init__(parent)
        self._state = get_state()
        self._is_dark = self._state.theme.is_dark if self._state.theme else is_dark

        # Use the central ThemeManager if available, else create a local one
        if self._state.theme:
            self._tm = self._state.theme
        else:
            self._tm = ThemeManager(self._is_dark)

        self._ctrl = DisplayController()
        self._build_ui()
        self._header.theme_toggle.toggled.connect(self._on_theme_toggle)
        self._state.lang.on_change(lambda _code: self.retranslate_ui())
        self._tm.apply(self)





    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addStretch()

        # ── header bar ────────────────────────────────────────────────────────
        root.addWidget(self._build_header())
        root.addStretch()
 
        self._panel = DisplayConfigPanel(self._ctrl)
        root.addWidget(self._panel, 1)
        self.setLayout(root)
        
    def _build_header(self) -> QWidget:
        self._header = Header(show_back=True)
        self._header.back_requested.connect(self.back_requested.emit)
        return self._header

    def showEvent(self, event):
        super().showEvent(event)
        if self._state.theme:
            is_dark = self._state.theme.is_dark
            if is_dark != self._is_dark:
                self._is_dark = is_dark
                self._tm.set_dark(is_dark)
                self._tm.apply(self)
        self._header.sync_theme()

    def retranslate_ui(self) -> None:
        I18nMixin._do_retranslate(self)  # Updates back_btn and other top-level bindings
        if hasattr(self, "_panel"):
            self._panel.retranslate_ui()


    def _on_theme_toggle(self, is_dark: bool):
        self._is_dark = is_dark
        self._tm.set_dark(is_dark)
        self._state.set("is_dark", is_dark)
        self._tm.apply(self)
        log.info("Config theme toggled: is_dark=%s", is_dark)

   