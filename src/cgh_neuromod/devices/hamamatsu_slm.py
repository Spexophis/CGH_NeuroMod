# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


import ctypes as ct

class HamamatsuSLM:
    def __init__(self, logg=None):
        self.logg = logg or self.setup_logging()


    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    def close(self):
        pass
