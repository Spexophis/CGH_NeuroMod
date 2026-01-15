# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from . import hamamatsu_slm


class DeviceManager:
    def __init__(self, logg=None, path=None):
        self.logg = logg or self.setup_logging()
        self.data_folder = path
        try:
            self.slm = hamamatsu_slm.HamamatsuSLM(logg=self.logg)
        except Exception as e:
            self.logg.error(f"{e}")
        self.logg.info("Finish initiating devices")

    def close(self):
        try:
            self.slm.close()
        except Exception as e:
            self.logg.error(f"{e}")

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging
