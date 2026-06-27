

import ctypes
import logging
import sys
import os

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QMainWindow, QStackedWidget, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QIcon

from core.app_state import get_state
from core.language_manager import LanguageManager
from ui.themes.theme import ThemeManager
from ui.windows.launch.launcher_window import MediaBridgeLauncher
from ui.windows.config.dual.config_dual import ConfigWindowDual
from ui.windows.config.display.config_display import ConfigWindowDisplay
from ui.windows.config.control.config_control import ConfigWindowControl
from ui.windows.control.control_mode import ControlMode
from ui.widgets.virtual_keyboard import VirtualKeyboard
from ui.widgets.touch_scroll import TouchScrollFilter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mediabridge")
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # PyInstaller temp extraction folder
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, "ui", "assets", "images", "mblogo.ico")

if sys.platform == "win32":
    myappid = "rs.mediabridge.app.1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class GlobalClickFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            # Close combo popups only if the click is NOT inside a popup
            clicked_widget = QApplication.widgetAt(event.globalPosition().toPoint())
            is_popup_click = False
            if clicked_widget:
                # Walk up to see if it's inside a QComboBox popup view
                w = clicked_widget
                while w:
                    if isinstance(w, QComboBox):
                        is_popup_click = True
                        break
                    # QListView inside a combo popup
                    if hasattr(w, 'parent') and isinstance(w.parent(), QComboBox):
                        is_popup_click = True
                        break
                    w = w.parent() if hasattr(w, 'parent') else None
            if not is_popup_click:
                for widget in QApplication.topLevelWidgets():
                    for combo in widget.findChildren(QComboBox):
                        combo.hidePopup()
        # Enable virtual keyboard for text inputs on focus
        if event.type() == QEvent.Type.FocusIn:
            if isinstance(obj, (QLineEdit, QTextEdit)):
                obj.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaBridge")
        self.setWindowIcon(QIcon(icon_path))
        # Adapt window size to screen — support 7" (1024×600) and up
        app = QApplication.instance()
        if app:
            geo = app.primaryScreen().availableGeometry()
            w = min(960, geo.width())
            h = min(680, geo.height())
            self.resize(w, h)
        else:
            self.resize(960, 680)

        # ── Main window stack ─────────────────────────────────────────────────────
        container = QWidget()
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        stack = QStackedWidget()
        container_lay.addWidget(stack, 1)
        


        self.setCentralWidget(container)
        stack.setWindowTitle("MediaBridge")
        stack.show()
        state = get_state()
        state.theme = ThemeManager(is_dark=True)
        state.lang = LanguageManager.instance()
        log.info("Central managers initialised (theme=%s, lang=%s)",
                "dark" if state.theme.is_dark else "light",
                state.lang.current)

        # Apply full theme QSS on the main window — cascades to all children
        state.theme.apply(self)
        state.subscribe("is_dark", lambda _: state.theme.apply(self))

        launcher = MediaBridgeLauncher(stack, main_window=self)
        config_dual = ConfigWindowDual(stack)
        config_display = ConfigWindowDisplay(stack)
        config_control = ConfigWindowControl(stack)

        stack.addWidget(launcher)   # index 0
        stack.addWidget(config_dual)     # index 1
        stack.addWidget(config_display)  # index 2
        stack.addWidget(config_control)  # index 3

        # Wire navigation signals
        launcher.launch_requested.connect(self.launchMode)
        config_dual.back_requested.connect(lambda: stack.setCurrentIndex(0))
        config_display.back_requested.connect(lambda: stack.setCurrentIndex(0))
        config_control.back_requested.connect(lambda: stack.setCurrentIndex(0))
        config_control.launch_requested.connect(lambda cfg: self._launch_control(cfg, stack))

        stack.setCurrentIndex(0)
        self._click_filter = GlobalClickFilter(self)
        self.installEventFilter(self._click_filter)

        self._stack = stack  # Keep reference for launchMode

        # Virtual keyboard — overlay (not in layout)
        self._vkb_enabled = True
        self._vkb = VirtualKeyboard(parent=container)

        # Attach keyboard to text inputs across all views
        self._kb_attached_ids: set[int] = set()
        self._attach_keyboard_to_views(launcher, config_dual, config_display, config_control)
    
    def moveEvent(self, event):
        """Close all dropdowns when the window is moved/dragged."""
        for combo in self.findChildren(QComboBox):
            combo.hidePopup()
        super().moveEvent(event)

    def launchMode(self, mode_id):
        log.info("Launch requested for mode '%s'", mode_id)
        if mode_id == "dual":
            self._stack.setCurrentIndex(1)
        elif mode_id == "display":
            self._stack.setCurrentIndex(2)
        elif mode_id == "control":
            self._stack.setCurrentIndex(3)
        else:
            log.warning("Unknown mode_id '%s'", mode_id)


    def set_virtual_keyboard_enabled(self, enabled: bool) -> None:
        """Globally enable/disable the shared virtual keyboard."""
        self._vkb_enabled = bool(enabled)
        self._vkb.set_enabled(self._vkb_enabled)

    def is_virtual_keyboard_enabled(self) -> bool:
        return self._vkb_enabled

    def _attach_keyboard_to_views(self, *views):
        """Attach keyboard to all text input fields in the given views."""
        for view in views:
            for cls in (QLineEdit, QTextEdit):
                for w in view.findChildren(cls):
                    wid = id(w)
                    if wid not in self._kb_attached_ids:
                        self._vkb.attach(w)
                        self._kb_attached_ids.add(wid)

    def _on_dual_exit(self, stack):
        """Called when exit gesture closes the kiosk — return to config."""
        log.info("Dual mode exited — returning to config")
        self._dual_mode = None
        self._vkb.close_kb()  # Close the keyboard when exiting kiosk mode
        stack.setCurrentIndex(1)
        self.show()

    def _launch_control(self, cfg: dict, stack):
        """Launch the control mode from config."""
        log.info("Launching control mode: %s", cfg.get("sub_mode", "media"))
        state = get_state()
        tm = state.theme

        sub_mode = cfg.get("sub_mode", "media")
        media_cfg = cfg.get("media", {})
        rest_cfg = cfg.get("restaurant", {})

        self._control_mode = ControlMode(
            sub_mode=sub_mode,
            tm=tm,
            local_dir=media_cfg.get("local_dir"),
            remote_url=media_cfg.get("remote_url"),
            remote_headers=media_cfg.get("remote_headers"),
            screensaver_cfg=media_cfg.get("screensaver"),
            menu_source=rest_cfg.get("menu_source"),
            restaurant_cfg=rest_cfg,
            on_exit=lambda: self._on_control_exit(stack),
            on_order=lambda order: log.info("Order received: %d items", len(order)),
        )
        self.hide()
        self._control_mode.launch(screen_index=cfg.get("screen_index"))

    def _on_control_exit(self, stack):
        """Called when exit gesture closes the control kiosk."""
        log.info("Control mode exited — returning to config")
        self._control_mode = None
        self._vkb.close_kb()  # Close the keyboard when exiting kiosk mode
        stack.setCurrentIndex(3)
        self.show()

def set_windows_app_id():
    if sys.platform.startswith("win"):
        app_id = "com.yourcompany.mediabridge"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

def main():
    # DPI consistency across platforms
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    set_windows_app_id()

    app = QApplication(sys.argv)
        # ── Touch-flick scroll (global, covers every QAbstractScrollArea) ──────
    app.setAttribute(Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTouchEvents, False)
    _touch_scroll = TouchScrollFilter(app)
    app.installEventFilter(_touch_scroll)

    # app_icon = QtGui.QIcon()
    # app_icon.addFile('./ui/assets/images/mblogo.ico', QtCore.QSize(256, 256))
    app.setWindowIcon(QIcon(icon_path))
    app.processEvents()
    app.setStyle("Fusion")
    # Install global event filter for combo popup closing + virtual keyboard
    _click_filter = GlobalClickFilter(app)
    app.installEventFilter(_click_filter)
    log.info("Application started")
    win = MainWindow()
    win.show()

    geo = app.primaryScreen().availableGeometry()
    win.move(
        geo.x() + (geo.width()  - win.width())  // 2,
        geo.y() + (geo.height() - win.height()) // 2,
    )
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

    