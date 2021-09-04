from pynes import *

NES_HSIZE = 0x0010
PROG_ROM_UNIT_SIZE = 0x4000
CHAR_ROM_UNIT_SIZE = 0x2000

logger = PynesLogger.get_logger(__name__)

class Cassette:
    def __init__(self, path):
        self.path = Path(path)
        self.size = self.path.stat().st_size

        content = self.path.read_bytes()
        self.prog_size = content[4] * PROG_ROM_UNIT_SIZE
        self.char_size = content[5] * CHAR_ROM_UNIT_SIZE
        pprint(vars(self))

        prog_rom_s = NES_HSIZE
        prog_rom_e = char_rom_s = NES_HSIZE + self.prog_size
        char_rom_e = char_rom_s + self.char_size
        logger.info(f"{prog_rom_s} {hex(prog_rom_e)}")
        logger.info(f"{char_rom_s} {hex(char_rom_e)}")
        self.prog_rom = content[prog_rom_s:prog_rom_e]
        self.char_rom = content[char_rom_s:char_rom_e]

        # hexdump(self.prog_rom)
        # hexdump(self.char_rom)