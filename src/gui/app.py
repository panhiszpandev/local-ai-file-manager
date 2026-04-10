import sys

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.gui.main_window import MainWindow
from src.gui.settings_dialog import SettingsDialog


class App:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.window = MainWindow()
        self.tray = self._create_tray()

        self.window.show()

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(self.qt_app)
        tray.setToolTip("AI File Manager")

        icon = QIcon.fromTheme("folder")
        tray.setIcon(icon)

        menu = QMenu()

        show_action = QAction("Show Window", menu)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        settings_action = QAction("Settings…", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()

        return tray

    def _show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _show_settings(self):
        dialog = SettingsDialog(self.window)
        dialog.exec()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_window()

    def _quit(self):
        if self.window.worker and self.window.worker.isRunning():
            self.window.worker.stop()
            self.window.worker.wait()
        self.qt_app.quit()

    def run(self) -> int:
        return self.qt_app.exec()
