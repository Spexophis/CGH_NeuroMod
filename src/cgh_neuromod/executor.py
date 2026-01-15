# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal

from . import run_threads


class CommandExecutor(QObject):
    svd = pyqtSignal(str)
    psv = pyqtSignal(str)

    def __init__(self, dev, cwd, cmp, path, logger=None):
        super().__init__()
        self.logg = logger or self.setup_logging()
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

    @pyqtSlot(str)
    def load_cgh_target(self, fd):
        pass

    @pyqtSlot(str)
    def save_cgh_pattern(self, fd):
        pass

    def cgh_computation(self):
        try:
            pass
        except Exception as e:
            self.logg.error(f"Error Running CGH Computation: {e}")
            return

    def run_cgh_computation(self):
        self.run_task(task=self.cgh_computation)
