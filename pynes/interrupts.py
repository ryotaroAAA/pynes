from pynes import *
from pynes.ram import *
logger = PynesLogger.get_logger(__name__)

class Interrupts:
    def __init__(self):
        self.irq = False
        self.nmi = False
    
    def get_irq_assert(self):
        return self.irq
    
    def get_nmi_assert(self):
        return self.nmi
    
    def assert_irq(self):
        self.irq = True
    
    def deassert_irq(self):
        self.irq = False
    
    def assert_nmi(self):
        self.nmi = True
    
    def deassert_nmi(self):
        self.nmi = False
