import pycobolt

from cgh_neuromod import logger


class CoboltLaser:

    def __init__(self, serial=None, com=None, logg=None):
        self.logg = logg or logger.setup_logging()
        self.serial_number = serial
        self.com_port = com
        self.laser = self._initiate_lasers()

    def _initiate_lasers(self):
        try:
            las = pycobolt.Cobolt06MLD(serialnumber=self.serial_number)
            las.send_cmd('@cobas 0')
            self.logg.info("{} Laser Connected".format(las))
            return las
        except Exception as e:
            self.logg.error(f"Laser Error: {e}")
            return None

    def close(self):
        self.laser_off()
        self.laser.disconnect()

    @staticmethod
    def setup_logging():
        import logging
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
        return logging

    @staticmethod
    def load_configs():
        import json
        config_file = input("Enter configuration file directory: ")
        with open(config_file, 'r') as f:
            cfg = json.load(f)
        return cfg

    def laser_off(self):
        self.laser.send_cmd('l0')

    def laser_on(self, laser):
        self.laser.send_cmd('l1')

    def set_constant_power(self, power):
        self.laser.constant_power(power)

    def set_constant_current(self, current):
        self.laser.constant_current(current)

    def set_modulation_mode(self, pw):
        self.laser.modulation_mode(pw)
        self.laser.digital_modulation(enable=1)
