# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from . import hamamatsu_slm, cobolt_laser
from cgh_neuromod import logger

class DeviceManager:
    def __init__(self, logg=None, path=None):
        self.logg = logg or logger.setup_logging()
        self.data_folder = path
        try:
            self.slm = hamamatsu_slm.HamamatsuSLM(serial_number="LSH0805629", logg=self.logg)
        except Exception as e:
            self.logg.error(f"{e}")
        try:
            self.laser = cobolt_laser.CoboltLaser(logg=self.logg)
        except Exception as e:
            self.logg.error(f"Laser init failed: {e}")

    def close(self):
        try:
            self.slm.close()
        except Exception as e:
            self.logg.error(f"{e}")
        try:
            self.laser.close()
        except Exception as e:
            self.logg.error(f"{e}")
