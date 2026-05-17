"""
Bootstraps the application:
  1. Configures logging
  2. Creates the QApplication
  3. Initialises the central managers (ThemeManager, LanguageManager)
     and wires them into AppState
  4. Builds the QStackedWidget with Launcher → Config navigation
"""

import logging
import sys

from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QMainWindow, QStackedWidget
from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtCore import QEvent, QObject

from core.app_state import get_state
from core.language_manager import LanguageManager
from ui.themes.theme import ThemeManager
from ui.windows.launch.launcher_window import MediaBridgeLauncher
from ui.windows.config.config_window import ConfigWindow

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mediabridge")




def center_window(window):
    """Centre *window* on its current screen."""
    wh = window.windowHandle()
    if wh is None:
        return
    screen = wh.screen()
    if screen is None:
        return

    frame = window.frameGeometry()
    screen_geo = screen.availableGeometry()

    x = screen_geo.x() + (screen_geo.width() - frame.width()) // 2
    y = screen_geo.y() + (screen_geo.height() - frame.height()) // 2
    y = max(y, screen_geo.y())

    window.move(x, y)

class GlobalClickFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            # Close all combo popups on any click
            for widget in QApplication.topLevelWidgets():
                for combo in widget.findChildren(QComboBox):
                    combo.hidePopup()
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaBridge")
        self.setFixedSize(960, 680)

        # ── Main window stack ─────────────────────────────────────────────────────
        stack = QStackedWidget()
        self.setCentralWidget(stack)
        stack.setWindowTitle("MediaBridge")
        stack.show()

        # ── Bootstrap central managers ────────────────────────────────────────────
        state = get_state()
        state.theme = ThemeManager(is_dark=True)
        state.lang = LanguageManager.instance()
        log.info("Central managers initialised (theme=%s, lang=%s)",
                "dark" if state.theme.is_dark else "light",
                state.lang.current)



        launcher = MediaBridgeLauncher(stack)
        config = ConfigWindow(stack)

        stack.addWidget(launcher)   # index 0
        stack.addWidget(config)     # index 1

        # Wire navigation signals
        launcher.launch_requested.connect(lambda: stack.setCurrentIndex(1))
        config.back_requested.connect(lambda: stack.setCurrentIndex(0))

        stack.setCurrentIndex(0)
        self._click_filter = GlobalClickFilter(self)
        self.installEventFilter(self._click_filter)
    def moveEvent(self, event):
        """Close all dropdowns when the window is moved/dragged."""
        for combo in self.findChildren(QComboBox):
            combo.hidePopup()
        super().moveEvent(event)
        


def main():
    # DPI consistency across platforms
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Force Qt to finish layout + WM negotiation
    app.processEvents()

    app.setStyle("Fusion")
    log.info("Application started")
    win = MainWindow()
    win.show()
    center_window(win)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
