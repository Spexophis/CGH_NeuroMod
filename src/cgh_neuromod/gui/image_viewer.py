# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QHBoxLayout


class ImgViewer(QWidget):

    def __init__(self, logg, parent=None):
        super().__init__(parent)
        self.logg = logg
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Vertical)

        plot_widget = QWidget()
        plot_layout = self._create_plot_widgets()
        plot_widget.setLayout(plot_layout)
        splitter.addWidget(plot_widget)

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
        self.target_img_item.setImage(img2d, autoLevels=(levels is None))
        if levels is not None:
            self.target_img_item.setLevels(levels)

    def set_pattern_image(self, img2d: np.ndarray, levels=None):
        self.pattern_img_item.setImage(img2d, autoLevels=(levels is None))
        if levels is not None:
            self.pattern_img_item.setLevels(levels)
