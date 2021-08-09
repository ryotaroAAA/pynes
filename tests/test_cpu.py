import pytest
from pynes.cassette import *
from pynes.cpu import *

@pytest.fixture
def hello_cpu():
    hello_cas = Cassette("rom/hello.nes")
    cpu = Cpu(hello_cas)
    cpu.load_correct_log("log/hello.yaml")
    return cpu

@pytest.mark.parametrize(("reg", "val"), [
    ("A", 0x00),
    ("X", 0x00),
    ("Y", 0x00),
    ("SP", 0x01FD),
    ("PC", 0x8000), # hello.nes entry point
])
def test_init_value(hello_cpu, reg, val):
    assert vars(hello_cpu.reg)[reg] == val

def test_status(hello_cpu):
    # compare with correct register status
    for _ in range(200):
        hello_cpu.run()

# @pytest.mark.parametrize(("addr", "val"), [
#     ("A", 0x00),
#     ("X", 0x00),
#     ("Y", 0x00),
#     ("SP", 0x01FD),
#     ("PC", 0x8000), # hello.nes entry point
# ])
# def test_read_write(cpu, reg, val):
#     assert vars(cpu.reg)[reg] == val