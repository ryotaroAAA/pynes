from pathlib import Path

from hexdump import hexdump
from tabulate import tabulate

NES_HSIZE = 0x0010
PROG_ROM_UNIT_SIZE = 0x4000
CHAR_ROM_UNIT_SIZE = 0x2000

class Cassette:
    def __init__(self, path):
        self.path = Path(path)
        self.size = self.path.stat().st_size

        content = self.path.read_bytes()
        self.prog_size = content[4] * PROG_ROM_UNIT_SIZE
        self.char_size = content[5] * CHAR_ROM_UNIT_SIZE
        print(vars(self))

        prog_rom_s = NES_HSIZE
        prog_rom_e = char_rom_s = NES_HSIZE + self.prog_size
        char_rom_e = char_rom_s + self.char_size
        print(prog_rom_s,hex(prog_rom_e))
        print(char_rom_s,hex(char_rom_e))
        self.prog_rom = content[prog_rom_s:prog_rom_e]
        self.char_rom = content[char_rom_s:char_rom_e]
    
    def print_prog_rom(self, addr, r = 100):
        hexdump(self.prog_rom[:])

    def print_char_rom(self, addr, r = 100):
        hexdump(self.char_rom[addr - r : addr + r])