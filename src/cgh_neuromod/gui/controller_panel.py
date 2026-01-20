# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import os
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QApplication
from cgh_neuromod import logger
from . import custom_widgets as cw

def select_file_from_folder(parent, data_folder):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Select a File", data_folder, "All Files (*)")
    return file_path if file_path else None


def get_file_dialog(fd):
    file_dialog = cw.FileDialogWidget(name="Save Pattern", file_filter="All Files (*)", default_dir=fd)
    if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
        selected_file = file_dialog.selectedFiles()
        if selected_file:
            return os.path.basename(selected_file[0])
        else:
            return None
    return None


def refresh_gui():
    QApplication.processEvents()


class ControlPanel(QWidget):
    Signal_load_target = pyqtSignal(str)
    Signal_pick_spot = pyqtSignal()
    Signal_compute_cgh = pyqtSignal()
    Signal_save_pattern = pyqtSignal(str)
    Signal_slm_correction = pyqtSignal(str)
    Signal_slm_load = pyqtSignal(str)
    Signal_slm_set = pyqtSignal()

    def __init__(self, df, logg=None, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.logg = logg or logger.setup_logging()
        self.data_folder = df
        self._setup_ui()
        self._set_signal_connections()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.cgh_panel = self._create_cgh_panel()
        self.slm_panel = self._create_slm_panel()

        main_layout.addWidget(self.cgh_panel)
        main_layout.addWidget(self.slm_panel)

        self.dialog, self.dialog_text = cw.create_dialog(labtex=True, interrupt=False)
        self.dialog.setModal(True)

        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def _create_cgh_panel(self):
        group = cw.GroupWidget()
        cgh_scroll_area, cgh_scroll_layout = cw.create_scroll_area("G")

        self.QPushButton_CGH_Load = cw.PushButtonWidget('Load Target')
        self.QPushButton_CGH_Pick = cw.PushButtonWidget('Pick Spots')
        self.QSpinBox_CGH_Iteration = cw.SpinBoxWidget(0, 1024, 1, 128)
        self.QDoubleSpinBox_CGH_Magnification = cw.DoubleSpinBoxWidget(0, 128, 1, 1, 7)
        self.QSpinBox_CGH_CenterX = cw.SpinBoxWidget(0, 2048, 1, 600)
        self.QSpinBox_CGH_CenterY = cw.SpinBoxWidget(0, 2048, 1, 395)
        self.QPushButton_CGH_Compute = cw.PushButtonWidget('Compute CGH')
        self.QPushButton_CGH_Save = cw.PushButtonWidget('Save CGH')

        cgh_scroll_layout.addWidget(cw.LabelWidget(str('CGH Computation')), 0, 0, 1, 1)
        cgh_scroll_layout.addWidget(cw.FrameWidget(), 1, 0, 1, 3)
        cgh_scroll_layout.addWidget(self.QPushButton_CGH_Load, 2, 0, 1, 1)
        cgh_scroll_layout.addWidget(self.QPushButton_CGH_Pick, 3, 0, 1, 1)
        cgh_scroll_layout.addWidget(cw.LabelWidget(str('Iterations')), 2, 1, 1, 1)
        cgh_scroll_layout.addWidget(self.QSpinBox_CGH_Iteration, 2, 2, 1, 1)
        cgh_scroll_layout.addWidget(cw.LabelWidget(str('Magnification')), 3, 1, 1, 1)
        cgh_scroll_layout.addWidget(self.QDoubleSpinBox_CGH_Magnification, 3, 2, 1, 1)
        cgh_scroll_layout.addWidget(cw.LabelWidget(str('Center-X')), 4, 1, 1, 1)
        cgh_scroll_layout.addWidget(self.QSpinBox_CGH_CenterX, 4, 2, 1, 1)
        cgh_scroll_layout.addWidget(cw.LabelWidget(str('Center-Y')), 5, 1, 1, 1)
        cgh_scroll_layout.addWidget(self.QSpinBox_CGH_CenterY, 5, 2, 1, 1)
        cgh_scroll_layout.addWidget(self.QPushButton_CGH_Compute, 4, 0, 1, 1)
        cgh_scroll_layout.addWidget(self.QPushButton_CGH_Save, 5, 0, 1, 1)

        group_layout = QHBoxLayout(group)
        group_layout.addWidget(cgh_scroll_area)
        group.setLayout(group_layout)
        return group

    def _create_slm_panel(self):
        group = cw.GroupWidget()
        slm_scroll_area, slm_scroll_layout = cw.create_scroll_area("G")

        self.QPushButton_SLM_Correction = cw.PushButtonWidget('Load Correction')
        self.QPushButton_SLM_Load = cw.PushButtonWidget('Load Pattern')
        self.QPushButton_SLM_Set = cw.PushButtonWidget('Apply Pattern')
        self.QSpinBox_SLM_OffsetX = cw.SpinBoxWidget(0, 1024, 1, 0)
        self.QSpinBox_SLM_OffsetY = cw.SpinBoxWidget(0, 1024, 1, 0)
        self.QDoubleSpinBox_SLM_Focal = cw.DoubleSpinBoxWidget(0, 2000, 1, 2, 180)

        slm_scroll_layout.addWidget(cw.LabelWidget(str('Hamamatsu SLM')), 0, 0, 1, 1)
        slm_scroll_layout.addWidget(cw.FrameWidget(), 1, 0, 1, 3)
        slm_scroll_layout.addWidget(self.QPushButton_SLM_Correction, 2, 0, 1, 1)
        slm_scroll_layout.addWidget(self.QPushButton_SLM_Load, 3, 0, 1, 1)
        slm_scroll_layout.addWidget(self.QPushButton_SLM_Set, 4, 0, 1, 1)
        slm_scroll_layout.addWidget(cw.LabelWidget(str('Offset X')), 2, 1, 1, 1)
        slm_scroll_layout.addWidget(self.QSpinBox_SLM_OffsetX, 2, 2, 1, 1)
        slm_scroll_layout.addWidget(cw.LabelWidget(str('Offset Y')), 3, 1, 1, 1)
        slm_scroll_layout.addWidget(self.QSpinBox_SLM_OffsetY, 3, 2, 1, 1)
        slm_scroll_layout.addWidget(cw.LabelWidget(str('Offset Y')), 3, 1, 1, 1)
        slm_scroll_layout.addWidget(self.QSpinBox_SLM_OffsetY, 3, 2, 1, 1)
        slm_scroll_layout.addWidget(cw.LabelWidget(str('Focal Length')), 4, 1, 1, 1)
        slm_scroll_layout.addWidget(self.QDoubleSpinBox_SLM_Focal, 4, 2, 1, 1)

        group_layout = QHBoxLayout(group)
        group_layout.addWidget(slm_scroll_area)
        group.setLayout(group_layout)
        return group

    def _set_signal_connections(self):
        self.QPushButton_CGH_Load.clicked.connect(self.load_target)
        self.QPushButton_CGH_Pick.clicked.connect(self.pick_spot)
        self.QPushButton_CGH_Compute.clicked.connect(self.compute_cgh)
        self.QPushButton_CGH_Save.clicked.connect(self.save_pattern)
        self.QPushButton_SLM_Correction.clicked.connect(self.set_slm_correction)
        self.QPushButton_SLM_Load.clicked.connect(self.load_slm_pattern)
        self.QPushButton_SLM_Set.clicked.connect(self.set_slm_pattern)

    def get_file_name(self):
        selected_file = select_file_from_folder(None, self.data_folder)
        if not selected_file:
            self.logg.error("No file selected.")
            return None
        else:
            self.logg.info(f"Selected file: {selected_file}")
            return selected_file

    @pyqtSlot()
    def load_target(self):
        file_name = self.get_file_name()
        if file_name is not None:
            self.Signal_load_target.emit(str(file_name))

    @pyqtSlot()
    def pick_spot(self):
        self.Signal_pick_spot.emit()
        print("Start target picking")

    @pyqtSlot()
    def compute_cgh(self):
        self.Signal_compute_cgh.emit()
        self.show_dialog(txt="CGH Computation")

    @pyqtSlot()
    def save_pattern(self):
        file_name = get_file_dialog(self.data_folder)
        if not file_name:
            self.logg.error("No file name.")
        else:
            self.logg.info(f"File name: {file_name}")
            self.Signal_save_pattern.emit(str(file_name))

    def show_dialog(self, txt):
        self.dialog.show()
        self.dialog_text.setText(f"Task {txt} is running, please wait...")
        refresh_gui()

    @pyqtSlot()
    def set_slm_correction(self):
        file_name = self.get_file_name()
        if file_name is not None:
            self.Signal_slm_correction.emit(str(file_name))

    @pyqtSlot()
    def load_slm_pattern(self):
        selected_file = select_file_from_folder(None, self.data_folder)
        if not selected_file:
            self.logg.error("No file selected.")
        else:
            self.logg.info(f"Selected file: {selected_file}")
            self.Signal_slm_load.emit(str(selected_file))

    @pyqtSlot()
    def set_slm_pattern(self):
        self.Signal_slm_set.emit()

    def get_cgh_parameters(self):
        n  = self.QSpinBox_CGH_Iteration.value()
        m = self.QDoubleSpinBox_CGH_Magnification.value()
        c0 = self.QSpinBox_CGH_CenterX.value()
        c1 = self.QSpinBox_CGH_CenterY.value()
        return n, m, (c0, c1)

    def get_slm_parameters(self):
        ox = self.QSpinBox_SLM_OffsetX.value()
        oy = self.QSpinBox_SLM_OffsetY.value()
        f = self.QDoubleSpinBox_SLM_Focal.value()
        return ox, oy, f
