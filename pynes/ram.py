from pynes import *
logger = PynesLogger.get_logger(__name__)

class Ram:
    def __init__(self, size):
        self.size = size
        self.data = bytearray(size)