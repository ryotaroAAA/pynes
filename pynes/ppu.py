from logging import raiseExceptions
from numpy import int8
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
    |  4   | background pattern table 0:0x0000, 1:0x1000         |
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
H_SIZE_WITH_VBLANK = 262
CYCLE_PER_LINE = 341

@dataclass
class Sprite:
    data: list[list[int]]
    x: int = 0
    y: int = 0
    attr: int = 0
    def __init__(self):
        self.data = np.zeros((8, 8), dtype=np.int8)

@dataclass
class Tile:
    sprite: Sprite
    palette_id: int = 0
    scroll_x: int = 0
    scroll_y: int = 0
    sprite_id: int = 0
    def __init__(self):
        self.sprite = Sprite()

@dataclass
class Image:
    sprite: list[Sprite] = field(default_factory=list)
    background: list[Tile] = field(default_factory=list)
    palette: list[int] = field(default_factory=list)

class Palette(Ram):
    def __init__(self, size):
        super().__init__(size)

    def read(self):
        data = np.zeros(PALETTE_SIZE, dtype=np.int)
        for i, _ in enumerate(self.data):
            if self.is_sprite_mirror(i):
                data[i] = self.data[i - 0x10]
            elif self.is_background_mirror(i):
                data[i] = self.data[i - 0x10]
            else:
                data[i] = self.data[i]
        assert len(data) == PALETTE_SIZE, len(data)
        return data

    def write(self, addr, data):
        self.data[self.get_pallette_addr(addr)] = data

    def is_background_mirror(self, addr):
        return (addr == 0x04 or
            addr == 0x08 or
            addr == 0x0c)

    def is_sprite_mirror(self, addr):
        return (addr == 0x10 or
            addr == 0x14 or
            addr == 0x18 or
            addr == 0x1c)

    def get_palette_addr(self, addr):
        mirror_downed = addr % 0x20
        return ((mirror_downed - 0x10) if
            self.is_sprite_mirror(mirror_downed) else mirror_downed)

class SpriteRam(Ram):
    def __init__(self, size):
        super().__init__(size)
        self.valid_addr = set()

    def read(self, addr):
        return self.data[addr]

    def write(self, addr, data):
        self.data[addr] = data
        self.valid_addr.add(addr)

class Ppu:
    def __init__(self, cas, vram, interrupts):
        self.vram = vram
        self.cas = cas
        self.interrupts = interrupts
        
        # control register 1
        self.creg1 = 0
        # control register 2
        self.creg2 = 0
        # status register 
        self.sreg = 0
        self.sprites = []
        self.background = []
        self.palette = Palette(PALETTE_SIZE)
        self.char_ram = Ram(cas.char_size)
        for addr, data in enumerate(self.cas.char_rom):
            self.char_ram.data[addr] = data
        self.sprite_ram = SpriteRam(SPRITE_RAM_SIZE)

        self.cycle = 0
        self.line = 0
        self.vram_buf = 0
        self.vram_addr = 0x0000
        self.vram_offset = 0x0000
        self.sprite_ram_addr = 0x0000
        self.scroll_x = 0
        self.scroll_y = 0
        self.is_horizontal_scroll = True
        self.is_lower_vram_addr = False

    # Control Register 1, PPU memory increment
    def get_vram_offset(self):
        return 32 if (self.creg1 & 0x04) else 1

    # Control Register 1, Main Screen assignment by name table
    def get_name_table_id(self):
        return (self.creg1 & 0x03)

    # Control Register 1, Assert NMI when VBlank
    def has_vblank_irq_enabled(self):
        return bool(self.creg1 & 0x80)

    # Control Register 1, get background pattern table
    def get_background_table_offset(self):
        return 0x1000 if (self.creg1 & 0x10) else 0x0000

    # Control Register 1, get sprite pattern table
    def get_sprite_table_offset(self):
        return 0x1000 if (self.creg1 & 0x08) else 0x0000

    # Control Register 2, Enable sprite
    def get_is_background_enable(self):
        return bool(self.creg2 & 0x08)

    # Control Register 2, Enable sprite
    def get_is_sprite_enable(self):
        return bool(self.creg2 & 0x10)

    # PPU status register
    def set_sprite_hit(self):
        self.sreg |= 0x40

    # PPU status register
    def clear_sprite_hit(self):
        self.sreg &= 0xBF

    # PPU status register
    def set_vblank(self):
        # print("set_vlank")
        self.sreg |= 0x80

    # PPU status register
    def get_is_vblank(self):
        return bool(self.sreg & 0x80)

    # PPU status register
    def clear_vblank(self):
        self.sreg &= 0x7F

    def has_sprite_hit(self):
        # main screen y
        y = self.sprite_ram.read(0x00)
        return ((y == self.line) and
            self.get_is_background_enable() and
            self.get_is_sprite_enable())

    def get_scroll_tile_x(self):
        return self.scroll_x + int(((self.get_name_table_id() % 2) * 256) / 8)

    def get_scroll_tile_y(self):
        return self.scroll_y + int(((self.get_name_table_id() / 2) * 240) / 8)

    def get_tile_y(self):
        return int(self.line / 8) + self.get_scroll_tile_y() - 1

    def get_block_id(self, x, y):
        return (int((x % 4) / 2) + int((y % 4) / 2)) * 2

    # read from name_table
    def get_sprite_id(self, x, y, offset):
        tile_num = y * 32 + x
        sprite_addr = tile_num + offset
        # print("",x, y, tile_num, sprite_addr)
        data = self.vram.data[sprite_addr]
        return data

    def get_attribute(self, x, y, offset):
        addr = int(x / 4) + int(y / 4) * 8 + 0x03C0 + offset
        # TODO
        # return self.vram->read(self.mirror_down_sprite_addr(addr))
        return self.vram.data[addr]

    def get_palette(self):
        return self.palette.read()

    def calc_vram_addr(self):
        if (self.vram_addr >= 0x3000 and self.vram_addr < 0x3F00):
            return self.vram_addr - 0x3000
        else:
            return self.vram_addr - 0x2000

    def vram_read(self):
        buf = self.vram_buf
        if self.vram_addr >= 0x2000:
            # name table, attribute table, pallette
            addr = self.calc_vram_addr()
            self.vram_addr += self.get_vram_offset()
            # dprint("addr %p %d", addr, buf)
            if addr >= 0x3F00:
                # palette
                return self.vram.data[addr]
        else:
            # pattern table from charactor rom
            self.vram_buf = self.char_ram.data[self.vram_addr]
            self.vram_addr += self.get_vram_offset()
            # dprint("addr %p %d", self.vram_addr, self.vram_buf)
        return buf

    def read(self, addr):
        '''
        | bit  | description                                 |
        +------+---------------------------------------------+
        | 7    | 1: VBlank clear by reading this register    |
        | 6    | 1: sprite hit                               |
        | 5    | 0: less than 8, 1: 9 or more                |
        | 4-0  | invalid                                     |                                 
        |      | bit4 VRAM write flag [0: success, 1: fail]  |
        '''
        if addr == 0x0002:
            # PPUSTATUS
            status = self.sreg
            self.is_horizontal_scroll = True
            self.clear_vblank()
            # print(status)
            return status
        elif addr == 0x0004:
            # OAMADDR
            # TODO?
            return self.sprite_ram.read(self.sprite_ram_addr)
        elif addr == 0x0007:
            # PPUDATA
            return self.vram_read()

    def write_sprite_ram_addr(self, data):
        self.sprite_ram_addr = data

    def write_sprite_ram_data(self, data):
        # print("addr:", self.sprite_ram_addr, "data:", hex(data))    
        self.sprite_ram.write(self.sprite_ram_addr, data)
        self.sprite_ram_addr += 1

    def write_scroll_data(self, data):
        if self.is_horizontal_scroll:
            self.is_horizontal_scroll = False
            self.scroll_x = data & 0xFF
        else:
            self.scroll_y = data & 0xFF
            self.is_horizontal_scroll = True
    
    def write_vram_addr(self, data):
        if self.is_lower_vram_addr:
            # dprint("low add %p", data)
            self.vram_addr += data
            self.is_lower_vram_addr = False
        else:
            # dprint("high add %p", data<<8)
            self.vram_addr = data << 8
            self.is_lower_vram_addr = True

    def write_vram_data(self, data):
        # dprint("%p : %p %d", self.vram_addr, data, data)
        if self.vram_addr >= 0x2000:
            if (self.vram_addr >= 0x3F00 and self.vram_addr < 0x4000):
                # pallette
                # print(f"[palette write] addr:{hex(self.vram_addr)}, {hex(data)}")
                self.palette.data[self.vram_addr - 0x3F00] = data
            else:
                # name table, attr table
                # print(f"[vram write] addr:{self.calc_vram_addr()}, {data}")
                self.vram.data[self.calc_vram_addr()] = data
        else:
            # pattern table from charactor rom
            # print(f"[pattern write] addr:{hex(self.vram_addr)}, {hex(data)}")
            self.char_ram.data[self.vram_addr] = data
        self.vram_addr += self.get_vram_offset()

    def write(self, addr, data):
        if addr == 0x0000:
            # logger.info(f"addr:{addr} data:{data}")
            self.creg1 = data
        elif addr == 0x0001:
            # logger.info(f"addr:{addr} data:{data}")
            self.creg2 = data
        elif addr == 0x0003:
            # set sprite ram write addr
            # dprint("addr:%d, %p", addr)
            # logger.info(f"[sprite addr] addr:{addr} data:{data}")
            self.write_sprite_ram_addr(data)
        elif addr == 0x0004:
            # sprite ram write
            # dprint("data:%d, %p", addr)
            # logger.info(f"[sprite data] addr:{addr} data:{data}")
            self.write_sprite_ram_data(data)
        elif addr == 0x0005:
            # set scroll setting
            self.write_scroll_data(data)
        elif addr == 0x0006:
            # set vram write addr (first: high 8bit, second: low 8bit)
            # logger.info(f"[vram addr write] addr:{addr} data:{hex(data)}")
            self.write_vram_addr(data)
        elif addr == 0x0007:
            # sprite ram write
            # logger.info(f"[sprite ram write] addr:{addr} data:{hex(data)}")
            self.write_vram_data(data)
        else:
            # logger.info(f"[NotImplement] addr:{addr} data:{data}")
            raise NotImplementedError

    # vector<vector<> 
    def build_sprite_data(self, sprite_id, offset):
        '''
            Bit Planes                  Pixel Pattern (return value)
            [lower bit]
            $0xx0=$41  01000001
            $0xx1=$C2  11000010
            $0xx2=$44  01000100
            $0xx3=$48  01001000
            $0xx4=$10  00010000
            $0xx5=$20  00100000         .1.....3
            $0xx6=$40  01000000         11....3.
            $0xx7=$80  10000000  =====  .1...3..
            [higher bit]                .1..3...
            $0xx8=$01  00000001  =====  ...3.22.
            $0xx9=$02  00000010         ..3....2
            $0xxA=$04  00000100         .3....2.
            $0xxB=$08  00001000         3....222
            $0xxC=$16  00010110
            $0xxD=$21  00100001
            $0xxE=$42  01000010
            $0xxF=$87  10000111

            see https:#wiki.nesdev.com/w/index.php/PPU_pattern_tables
        '''
        sprite = np.zeros((8, 8), dtype=np.int)
        for i in range(0, 16):
            addr = sprite_id * 16 + i + offset
            ram = self.char_ram.data[addr]

            for j in range(0, 8):
                if ram & (0x80 >> j):
                    sprite[i % 8][j] += 0x01 << int(i/8)
        return sprite

    def build_sprites(self):
        # see https:#wiki.nesdev.com/w/index.php/PPU_OAM
        for i in range(0, self.sprite_ram_addr, 4):
            sprite = Sprite()
            sprite.y = self.sprite_ram.read(i)
            sprite_id = self.sprite_ram.read(i + 1)
            sprite.attr = self.sprite_ram.read(i + 2)
            sprite.x = self.sprite_ram.read(i + 3)
            sprite.data = \
                self.build_sprite_data(sprite_id, self.get_sprite_table_offset())
            # print(f"[{i}][{sprite_id}](x, y) = ({sprite.x}, {sprite.y})\n"
            #     f"{sprite.data}")
            self.sprites.append(sprite)

    # the element of background
    def build_tile(self, x, y, offset):
        tile = Tile()
        block_id = self.get_block_id(x, y)
        sprite_id = self.get_sprite_id(x, y, offset)
        attr = self.get_attribute(x, y, offset)
        tile.sprite_id = sprite_id
        tile.palette_id = (attr >> (block_id * 2)) & 0x03
        tile.sprite.data = self.build_sprite_data(sprite_id, 
                self.get_background_table_offset())
        tile.scroll_x = self.scroll_x
        tile.scroll_y = self.scroll_y
        return tile

    # draw every 8 line
    def build_background(self):
        mod_y = self.get_tile_y() % V_SPRITE_NUM
        table_id_offset = \
            2 if int((self.get_tile_y() / V_SPRITE_NUM) % 2) else 0

        for x in range(0, H_SPRITE_NUM):
            # tile_x = (x + self.get_scroll_tile_x())
            mod_x = x % H_SPRITE_NUM
            name_table_id = int(x / H_SPRITE_NUM) % 2 + table_id_offset
            offset_addr_by_name_table = name_table_id * 0x0400
            tile = self.build_tile(mod_x, mod_y, offset_addr_by_name_table)
            self.background.append(tile)

    def run(self, cycle):
        self.cycle += 3 * cycle
        
        if self.line == 0:
            self.background.clear()
            self.sprites.clear()
        if self.cycle >= CYCLE_PER_LINE:
            self.cycle -= CYCLE_PER_LINE
            self.line += 1

            if self.has_sprite_hit():
                self.set_sprite_hit()
            if self.line <= H_SIZE and \
                not (self.line % TILE_SIZE) and \
                    (self.line % TILE_SIZE == 0):
                self.build_background()
            
            if self.line == H_SIZE + 1:
                self.set_vblank()
                # raise Exception
                self.interrupts.deassert_nmi()
                if self.has_vblank_irq_enabled():
                    self.interrupts.deassert_nmi()
            
            if self.line == H_SIZE_WITH_VBLANK:
                self.build_sprites()
                self.clear_vblank()
                self.clear_sprite_hit()
                self.line = 0

                self.image = {}
                self.image["sprites"] = self.sprites
                self.image["background"] = self.background
                self.image["palette"] = self.get_palette()
                self.interrupts.deassert_nmi()
                return self.image
        return None