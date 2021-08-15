__version__ = '0.1.0'

from dataclasses import dataclass
from enum import auto, Enum
import logging
import logging.config
from pathlib import Path
import traceback
from typing import DefaultDict

from hexdump import hexdump
from pprint import *
from print_color import print
from tabulate import tabulate
import yaml

class PynesLogger:
    def __init__(self, logger):
        self.logger = logger

    @classmethod
    def get_logger(cls, name):
        if not hasattr(cls, "logger"):
            with Path("conf/logging.yaml").open() as f:
                logging_conf = yaml.safe_load(f)
            
            logging.config.dictConfig(logging_conf)
            logger = logging.getLogger(name)
            # cls(logger)
            return logger
        else:
            return cls.logger