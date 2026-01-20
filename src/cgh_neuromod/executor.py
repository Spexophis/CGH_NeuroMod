# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from cgh_neuromod import logger
from . import run_threads


class CommandExecutor(QObject):
    svd = pyqtSignal(str)
    task_finished = pyqtSignal()

    def __init__(self, dev, cwd, cmp, path, logg=None):
        super().__init__()
        self.logg = logg or logger.setup_logging()
        self.devs = dev
        self.vw = cwd
        self.ctrl_panel = self.vw.ctrl_panel
        self.viewer = self.vw.viewer
        self.cgh = cmp.cgh
        self.path = path
        self._set_signal_executions()
        self._initial_setup()
        self.task_worker = None

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    def _set_signal_executions(self):
        self.ctrl_panel.Signal_load_target.connect(self.load_cgh_target)
        self.ctrl_panel.Signal_compute_cgh.connect(self.run_cgh_computation)
        self.ctrl_panel.Signal_save_pattern.connect(self.save_cgh_pattern)
        self.ctrl_panel.Signal_slm_correction.connect(self.load_slm_correction)
        self.ctrl_panel.Signal_slm_load.connect(self.load_slm_pattern)
        self.ctrl_panel.Signal_set_laser.connect(self.set_laser)
        self.task_finished.connect(self.show_cgh_pattern)
        self.viewer.spots_picked.connect(self.cgh.load_spots_picked)

    def _initial_setup(self):
        try:
            self.logg.info("Finish setting up controllers")
        except Exception as e:
            self.logg.error(f"Initial setup Error: {e}")

    def run_task(self, task, iteration=1, parent=None):
        if getattr(self, "task_worker", None) is not None and self.task_worker.isRunning():
            return
        self.task_worker = run_threads.TaskWorker(task=task, n=iteration, parent=parent)
        self.task_worker.finished.connect(self.task_finish)
        self.task_worker.start()

    @pyqtSlot()
    def task_finish(self):
        w = self.task_worker
        self.task_worker = None
        w.deleteLater()
        self.ctrl_panel.dialog.close()
        self.task_finished.emit()

    @pyqtSlot(str)
    def load_cgh_target(self, fd):
        self.cgh.load_mask(fd)
        self.viewer.set_target_image(self.cgh.mask)

    @pyqtSlot()
    def update_cgh_parameters(self):
        n, m, c = self.ctrl_panel.get_cgh_parameters()
        o, f = self.ctrl_panel.get_slm_parameters()
        self.cgh.update_parameters(n, m, f * 1e-3, c)

    @pyqtSlot(str)
    def save_cgh_pattern(self, fd):
        self.cgh.save_cgh(str(self.path + r"\\" + fd))

    @pyqtSlot()
    def show_cgh_pattern(self):
        self.viewer.set_pattern_image(self.cgh.phase_total)

    def cgh_computation(self):
        try:
            self.update_cgh_parameters()
            self.cgh.compute_cgh()
        except Exception as e:
            self.logg.error(f"Error Running CGH Computation: {e}")
            return

    def run_cgh_computation(self):
        self.run_task(task=self.cgh_computation)

    @pyqtSlot(str)
    def load_slm_correction(self, fd: str):
        self.cgh.load_correction_pattern(fd)
        self.viewer.set_pattern_image(self.cgh.device.correction_pattern)

    @pyqtSlot(str)
    def load_slm_pattern(self, fd: str):
        self.devs.slm.load_pattern(fd)
        self.viewer.set_pattern_image(self.cgh.device.correction_pattern)

    @pyqtSlot(bool, bool, float)
    def set_laser(self, mod, sw, pw):
        if mod:
            self.devs.ls.set_modulation_mode(pw)
        else:
            self.devs.ls.set_constant_power(sw)
        if sw:
            self.devs.ls.laser_on()
        else:
            self.devs.ls.laser_off()
