# -*- coding: utf-8 -*-
# Copyright (c) 2025 Ruizhe Lin
# Licensed under the MIT License.


from . import cgh_pattern_generator


class ComputationManager:
    def __init__(self, logg=None):
        self.logg = logg or self.setup_logging()
        self.cgh = cgh_pattern_generator.CGH(logg=self.logg)

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging
