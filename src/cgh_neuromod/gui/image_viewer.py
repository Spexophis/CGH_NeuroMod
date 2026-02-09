# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QHBoxLayout, QLabel
from cgh_neuromod import logger
from . import custom_widgets as cw

class ImgViewer(QWidget):
    spots_picked = pyqtSignal(list)  # Emits list of (x, y, z, intensity) tuples

    def __init__(self, logg, parent=None):
        super().__init__(parent)
        self.logg = logg or logger.setup_logging()
        self._setup_ui()
        self._target_img = None
        self._picking_enabled = False
        self._picking_n = None
        self.target_points = []  # List of (x, y, z, intensity) tuples

        self.target_plot.scene().sigMouseClicked.connect(self._on_target_mouse_clicked)
        self.target_plot.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.target_plot.installEventFilter(self)

        self.target_spots_item = pg.ScatterPlotItem(size=10, pen=pg.mkPen(width=2))
        self.target_plot.addItem(self.target_spots_item)

        # Connect table changes to update overlay and emit signal
        self.spot_table.spots_changed.connect(self._on_table_spots_changed)


    def _setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Vertical)

        plot_widget = QWidget()
        plot_layout = self._create_plot_widgets()
        plot_widget.setLayout(plot_layout)
        splitter.addWidget(plot_widget)

        # Add spot table widget
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_label = QLabel("Spot Coordinates (editable - press Delete to remove selected row)")
        table_label.setStyleSheet("color: #CCCCCC; font-weight: bold; padding: 4px;")
        self.spot_table = cw.SpotTableWidget()
        table_layout.addWidget(table_label)
        table_layout.addWidget(self.spot_table)
        table_widget.setLayout(table_layout)
        splitter.addWidget(table_widget)

        # Set initial splitter sizes (plots larger than table)
        splitter.setSizes([400, 150])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_plot_widgets(self):
        layout_plot = QHBoxLayout()

        self.target_plot = pg.PlotWidget()
        self.target_plot.setAspectLocked(True)
        self.target_plot.getPlotItem().hideAxis("left")
        self.target_plot.getPlotItem().hideAxis("bottom")

        self.target_img_item = pg.ImageItem(axisOrder="row-major")  # numpy (H,W)
        self.target_plot.addItem(self.target_img_item)
        self.target_plot.invertY(True)
        
        self.pattern_plot = pg.PlotWidget()
        self.pattern_plot.setAspectLocked(True)
        self.pattern_plot.getPlotItem().hideAxis("left")
        self.pattern_plot.getPlotItem().hideAxis("bottom")

        self.pattern_img_item = pg.ImageItem(axisOrder="row-major")  # numpy (H,W)
        self.pattern_plot.addItem(self.pattern_img_item)
        self.pattern_plot.invertY(True)

        layout_plot.addWidget(self.target_plot, stretch=1)
        layout_plot.addWidget(self.pattern_plot, stretch=1)
        return layout_plot

    def set_target_image(self, img2d: np.ndarray, levels=None):
        self._target_img = img2d
        self.target_img_item.setImage(img2d, autoLevels=(levels is None))
        if levels is not None:
            self.target_img_item.setLevels(levels)
        h, w = img2d.shape[:2]
        self.target_plot.setLimits(xMin=0, xMax=w, yMin=0, yMax=h)
        self.target_plot.setRange(xRange=(0, w), yRange=(0, h), padding=0)

    def set_pattern_image(self, img2d: np.ndarray, levels=None):
        self.pattern_img_item.setImage(img2d, autoLevels=(levels is None))
        if levels is not None:
            self.pattern_img_item.setLevels(levels)

    def start_target_picking(self):
        print("Start picking...")
        self._picking_enabled = True

        self.target_points = []
        self.spot_table.clear_spots()
        self._update_target_spots_overlay()

        self.target_plot.setFocus()
        self.target_plot.setCursor(Qt.CursorShape.CrossCursor)

        self._update_pick_status()

    def finish_target_picking(self):
        self._picking_enabled = False
        self.target_plot.unsetCursor()
        self._update_pick_status(done=True)

        # Get the latest data from the table (in case user edited values)
        self.target_points = self.spot_table.get_spots()
        pts = list(self.target_points)
        self.spots_picked.emit(pts)

    def cancel_target_picking(self):
        self._picking_enabled = False
        self.target_plot.unsetCursor()
        self._update_pick_status(cancelled=True)

    def _update_pick_status(self, done=False, cancelled=False):
        n = len(getattr(self, "target_points", []))
        if cancelled:
            title = "Picking cancelled"
        elif done:
            title = f"Picked {n} spot(s)"
        elif self._picking_enabled:
            title = f"Picking: {n} spot(s)  |  Left-click add, Backspace undo, Enter finish, Esc cancel"
        else:
            title = f"Spots: {n}"

        self.target_plot.getPlotItem().setTitle(title)

    def _on_target_mouse_clicked(self, ev):
        if not self._picking_enabled or self._target_img is None:
            return

        # right-click = finish (optional)
        if ev.button() == Qt.MouseButton.RightButton:
            self.finish_target_picking()
            return

        if ev.button() != Qt.MouseButton.LeftButton:
            return

        vb = self.target_plot.getPlotItem().vb
        if not vb.sceneBoundingRect().contains(ev.scenePos()):
            return

        p = vb.mapSceneToView(ev.scenePos())
        x, y = float(p.x()), float(p.y())

        h, w = self._target_img.shape[:2]
        if not (0 <= x < w and 0 <= y < h):
            return

        u = int(round(x))
        v = int(round(y))
        # Store as (x, y, z, intensity) with default z=0 and intensity=1.0
        self.target_points.append((u, v, 0.0, 1.0))
        self.spot_table.add_spot(u, v, 0.0, 1.0)
        self._update_target_spots_overlay()
        self._update_pick_status()

    def _update_target_spots_overlay(self):
        if not self.target_points:
            self.target_spots_item.setData([], [])
            return
        xs = [p[0] for p in self.target_points]
        ys = [p[1] for p in self.target_points]
        self.target_spots_item.setData(xs, ys)

    def _on_table_spots_changed(self, spots):
        """Handle changes from the spot table (user edits)."""
        self.target_points = spots
        self._update_target_spots_overlay()
        self._update_pick_status()

    def eventFilter(self, obj, event):
        if obj is self.target_plot and self._picking_enabled:
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()

                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.finish_target_picking()
                    return True

                if key == Qt.Key.Key_Backspace:
                    if self.target_points:
                        self.target_points.pop()
                        self.spot_table.remove_last_spot()
                        self._update_target_spots_overlay()
                        self._update_pick_status()
                    return True

                if key == Qt.Key.Key_Escape:
                    self.cancel_target_picking()
                    return True

        return super().eventFilter(obj, event)
