from pynes import *
from pynes.ram import *
logger = PynesLogger.get_logger(__name__)

'''
    [Control Register1 0x2000]
    | bit  | description                                 |
    +------+---------------------------------------------+
    |  7   | Assert NMI when VBlank 0: disable, 1:enable |
    |  6   | PPU master/slave, always 1                  |
    |  5   | Sprite size 0: 8x8, 1: 8x16                 |
    |  4   | Bg pattern table 0:0x0000, 1:0x1000         |
    |  3   | sprite pattern table 0:0x0000, 1:0x1000     |
    |  2   | PPU memory increment 0: +=1, 1:+=32         |
    |  1-0 | Name table 0x00: 0x2000                     |
    |      |            0x01: 0x2400                     |
    |      |            0x02: 0x2800                     |
    |      |            0x03: 0x2C00                     |

    [Control Register2 0x2001]
    | bit  | description                                 |
    +------+---------------------------------------------+
    |  7-5 | Background color  0x00: Black               |
    |      |                   0x01: Green               |
    |      |                   0x02: Blue                |
    |      |                   0x04: Red                 |
    |  4   | Enable sprite                               |
    |  3   | Enable background                           |
    |  2   | Sprite mask       render left end           |
    |  1   | Background mask   render left end           |
    |  0   | Display type      0: color, 1: mono         |

    [PPU MEMORY MAP]
    | addr           |  description               |
    +----------------+----------------------------+
    | 0x0000-0x0FFF  |  Pattern table#0           |
    | 0x1000-0x1FFF  |  Pattern table#1           |
    | 0x2000-0x23BF  |  Name table                |
    | 0x23C0-0x23FF  |  Attribute table           |
    | 0x2400-0x27BF  |  Name table                |
    | 0x27C0-0x27FF  |  Attribute table           |
    | 0x2800-0x2BBF  |  Name table                |
    | 0x2BC0-0x2BFF  |  Attribute table           |
    | 0x2C00-0x2FBF  |  Name Table                |
    | 0x2FC0-0x2FFF  |  Attribute Table           |
    | 0x3000-0x3EFF  |  mirror of 0x2000-0x2EFF   |
    | 0x3F00-0x3F0F  |  background Palette        |
    | 0x3F10-0x3F1F  |  sprite Palette            |
    | 0x3F20-0x3FFF  |  mirror of 0x3F00-0x3F1F   |
'''

SPRITE_RAM_SIZE = 0x0100
PALETTE_SIZE = 0x20
VRAM_SIZE = 0x0800
TILE_SIZE = 8
V_SPRITE_NUM = 30
H_SPRITE_NUM = 32
H_SIZE = 240
V_SIZE = 256
H_SIZE_WITH_VBLANK = 262
CYCLE_PER_LINE = 341

@dataclass
class Status:
    PPUCTRL: bool = False
    PPUMASK: bool = False
    PPUSTATUS: bool = True
    OAMADDR: bool = False
    OAMDATA: bool = False
    PPUSCROLL: bool = True
    PPUADDR: bool = False
    PPUDATA: bool = False

    def reset(self):
        self.PPUCTRL = False
        self.PPUMASK = False
        self.PPUSTATUS = True
        self.OAMADDR = False
        self.OAMDATA = False
        self.PPUSCROLL = True
        self.PPUADDR = False
        self.PPUDATA = False

    def get_val(self):
        p = (1 << 0) if self.PPUCTRL else 0
        p += (1 << 1) if self.PPUMASK else 0
        p += (1 << 2) if self.PPUSTATUS else 0
        p += (1 << 3) if self.OAMADDR else 0
        p += (1 << 4) if self.OAMDATA else 0
        p += (1 << 5) if self.PPUSCROLL else 0
        p += (1 << 6) if self.PPUADDR else 0
        p += (1 << 7) if self.PPUDATA else 0
        return p
    
    def set_val(self, p):
        self.PPUCTRL = p & (1 << 0) > 0
        self.PPUMASK = p & (1 << 1) > 0
        self.PPUSTATUS = p & (1 << 2) > 0
        self.OAMADDR = p & (1 << 3) > 0
        self.OAMDATA = p & (1 << 4) > 0
        self.PPUSCROLL = p & (1 << 5) > 0
        self.PPUADDR = p & (1 << 6) > 0
        self.PPUDATA = p & (1 << 7) > 0

@dataclass
class Sprite:
    data: list[list[int]] = field(default_factory=list)
    x: int = 0
    y: int = 0
    attr: int = 0

@dataclass
class Tile:
    data: Sprite = field(default_factory=Sprite)
    palette_id: int = 0
    scroll_x: int = 0
    scroll_y: int = 0
    sprite_id: int = 0

@dataclass
class Image:
    sprite: list[Sprite] = field(default_factory=list)
    bg: list[Tile] = field(default_factory=list)
    palette: list[int] = field(default_factory=list)

class Palette(Ram):
    def __init__(self, size):
        super.__init__(size)

    def read(self):
        data = []
        for i, _ in enumerate(self.data):
            if self.sprite_mirror(i):
                data.append(self.data[i - 0x10])
            if self.bg(i):
                data.append(self.data[i - 0x10])
            data.append(self.data(i))
        assert len(data) == PALETTE_SIZE
        return data

    def write(self, addr, data):
        self.data[self.get_pallette_addr(addr)] = data
    
    def is_bg_mirror(self, addr):
        logger.warn(f"Not Implement")
        return 0
    
    def is_sprite_mirror(self, addr):
        logger.warn(f"Not Implement")
        return 0
    
    def get_palette_addr(self, addr):
        logger.warn(f"Not Implement")
        return addr % 0x20

class Ppu:
    def __init__(self, vram, cas, interrupts):
        self.vram = vram
        self.cas = cas
        self.interrupts = interrupts
        
        self.palette = Palette(PALETTE_SIZE)
        self.char_ram = Ram(cas.get_char_size())
        for addr, data in enumerate(self.cas.get_char_rom()):
            self.char_ram.write(addr, data)
        self.sprite_ram = Ram(SPRITE_RAM_SIZE)

        self.vram_buf = 0
        self.vram_addr = 0x0000
        self.vram_offset = 0x0000
        self.sprite_ram_addr = 0x0000
        self.scroll_x = 0
        self.scroll_y = 0
        self.is_horizontal_scroll = True
        self.is_lower_vram_addr = False

    def run(self, cycle):
        self.cycle = cycle
        
        if self.line == 0:
            self.bg.clear()
            self.build_sprites()
        
        if self.cycle > CYCLE_PER_LINE:
            self.cycle -= CYCLE_PER_LINE
            self.line += 1

            if self.has_sprite_hit():
                self.set_sprite_hit()
            
            if self.line <= H_SIZE and \
                not (self.line % TILE_SIZE) and \
                    (self.line % TILE_SIZE == 0):
                self.build_bg()
            
            if self.line == H_SIZE + 1:
                self.set_vblank()
                # self.interrupts.deassert_nmi()
                if self.has_vblank_irq_enabled():
                    self.interrupts.deassert_nmi()
            
            if self.line == H_SIZE_WITH_VBLANK:
                self.clear_vblank()
                self.clear_sprite_hit()
                self.line = 0

                self.image.sprites = self.sprites
                self.image.bg = self.bg
                self.image.palette = self.get_palette()
                self.interrupts.deassert_nmi()
                return self.image
        return None