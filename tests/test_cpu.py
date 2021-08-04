import pytest
from pynes.cassette import *
from pynes.cpu import *

@pytest.fixture
def cpu():
    cas = Cassette("rom/hello.nes")
    return Cpu(cas)

@pytest.mark.parametrize(("reg", "val"), [
    ("A", 0x00),
    ("X", 0x00),
    ("Y", 0x00),
    ("SP", 0x01FD),
    ("PC", 0x8000), # hello.nes entry point
])
def test_init_value(cpu, reg, val):
    assert vars(cpu.reg)[reg] == val

# @pytest.mark.parametrize(("addr", "val"), [
#     ("A", 0x00),
#     ("X", 0x00),
#     ("Y", 0x00),
#     ("SP", 0x01FD),
#     ("PC", 0x8000), # hello.nes entry point
# ])
# def test_read_write(cpu, reg, val):
#     assert vars(cpu.reg)[reg] == val