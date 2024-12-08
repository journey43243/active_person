import logging
from patterns import Singleton

loggers = {}


class Logger(metaclass=Singleton):

    def __init__(self, name):
        self.name = name

    def get_logger(self):
        global loggers
        if loggers.get(self.name):
            return loggers.get(self.name)
        else:
            logger = logging.getLogger(self.name)
            logger.setLevel(logging.INFO)
            logger_handler = logging.FileHandler(f"logs/{self.name}.log", mode='a')
            logger_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
            logger_handler.setFormatter(logger_formatter)
            logger.addHandler(logger_handler)
            loggers[self.name] = logger
            return logger
