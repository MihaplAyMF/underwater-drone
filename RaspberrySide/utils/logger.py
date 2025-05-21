# Logger utility

import logging

class Logger:
    def __init__(self, log_file):
        self.logger = logging.getLogger("UnderwaterDrone")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(self, message):
        self.logger.info(message)
