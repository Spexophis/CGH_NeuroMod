# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import sys
import traceback

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow

from cgh_neuromod import logger
from . import controller_panel, image_viewer
from . import custom_widgets as cw

_orig = QtGui.QFont.setPointSize


def patched(self, size):
    if size <= 0:
        print(f"[BAD setPointSize({size})] family={self.family()} "
              f"pointSize={self.pointSize()} pixelSize={self.pixelSize()}")
        traceback.print_stack(limit=30)
    return _orig(self, size)


QtGui.QFont.setPointSize = patched


class MainWindow(QMainWindow):
    aboutToClose = pyqtSignal()

    def __init__(self, path=None, logg=None):
        super().__init__()
        self.logg = logg or logger.setup_logging()
        self.data_folder = path
        self._set_dark_theme()
        self._setup_ui()
        self._set_signal_connections()
        self.dialog, self.dialog_text = None, None

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    def closeEvent(self, event, **kwargs):
        self.aboutToClose.emit()
        super().closeEvent(event)

    def _setup_ui(self):
        self.ctrl_panel = controller_panel.ControlPanel(self.data_folder, self.logg)
        self.ctrl_dock = cw.DockWidget("Control Panel")
        self.ctrl_dock.setWidget(self.ctrl_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.ctrl_dock)

        self.viewer = image_viewer.ImgViewer(self.logg)
        self.setCentralWidget(self.viewer)

    def _set_signal_connections(self):
        self.ctrl_panel.Signal_pick_spot.connect(self.viewer.start_target_picking)

    def _set_dark_theme(self):
        dark_stylesheet = """
        QWidget {
            background-color: #232629;
            color: #f0f0f0;
            font-size: 12px;
        }
        QPushButton {
            background-color: #444;
            border: 1px solid #555;
            color: #f0f0f0;
            padding: 4px;
            border-radius: 2px;
        }
        QPushButton:hover {
            background-color: #666;
        }
        QLabel {
            color: #e0e0e0;
        }
        QSpinBox {
            background-color: #222;
            color: #f0f0f0;
            border: 1px solid #333;
        }
        QGroupBox {
            border: 1px solid #555;
            margin-top: 10px;
        }
        """
        self.setStyleSheet(dark_stylesheet)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
