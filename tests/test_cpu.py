import pytest
from pynes.cassette import *
from pynes.cpu import *
from pynes.ppu import *
from pynes.interrupts import *

@pytest.fixture
def hello_cpu():
    hello_cas = Cassette("rom/hello.nes")
    wram = Ram(WRAM_SIZE)
    vram = Ram(VRAM_SIZE)
    inter = Interrupts()
    ppu = Ppu(hello_cas, vram, inter)
    cpu = Cpu(hello_cas, wram, ppu, inter)
    cpu.load_correct_log("log/hello.yaml")
    return cpu

@pytest.fixture
def nestest_cpu(limit = 8991):
    cas = Cassette("rom/nestest.nes")
    wram = Ram(WRAM_SIZE)
    vram = Ram(VRAM_SIZE)
    inter = Interrupts()
    ppu = Ppu(cas, vram, inter)
    cpu = Cpu(cas, wram, ppu, inter)
    cpu.reset_addr(0xc000)
    cpu.load_correct_log(f"log/nestest{limit}.yaml")
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

def test_nestest(nestest_cpu, limit = 8991):
    cpu = nestest_cpu
    for _ in range(limit):
        try:
            cpu.run()
        except NotImplementedError:
            print(traceback.format_exc())
            print(f"{cpu.dump[-1]['opset']}, "
            f"{cpu.dump[-1]['mode']}",
                tag = "NotImplementedYet",
                tag_color = "yellow",
                color = "yellow")
            break