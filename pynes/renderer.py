from pynes import *
from pynes.ram import *
logger = PynesLogger.get_logger(__name__)

COLORS = [
    0x808080, 0x003DA6, 0x0012B0, 0x440096,
    0xA1005E, 0xC70028, 0xBA0600, 0x8C1700,
    0x5C2F00, 0x104500, 0x054A00, 0x00472E,
    0x004166, 0x000000, 0x050505, 0x050505,
    0xC7C7C7, 0x0077FF, 0x2155FF, 0x8237FA,
    0xEB2FB5, 0xFF2950, 0xFF2200, 0xD63200,
    0xC46200, 0x358000, 0x058F00, 0x008A55,
    0x0099CC, 0x212121, 0x090909, 0x090909,
    0xFFFFFF, 0x0FD7FF, 0x69A2FF, 0xD480FF,
    0xFF45F3, 0xFF618B, 0xFF8833, 0xFF9C12,
    0xFABC20, 0x9FE30E, 0x2BF035, 0x0CF0A4,
    0x05FBFF, 0x5E5E5E, 0x0D0D0D, 0x0D0D0D,
    0xFFFFFF, 0xA6FCFF, 0xB3ECFF, 0xDAABEB,
    0xFFA8F9, 0xFFABB3, 0xFFD2B0, 0xFFEFA6,
    0xFFF79C, 0xD7E895, 0xA6EDAF, 0xA2F2DA,
    0x99FFFC, 0xDDDDDD, 0x111111, 0x111111
]

class Renderer:
    def __init__(self):
        self.data = np.zeros((H_SIZE, V_SIZE), dtype=np.int)

    def render(self, image):
        self.image = image
        if not image["background"] == None:
            self.render_background()
        if not image["sprites"] == None:
            self.render_sprites()
    
    def get_render_result(self):
        return self.data
    
    def should_pixel_hide(self, x, y):
        tile_x = int(x/8)
        tile_y = int(y/8)
        index = tile_y * 32 + tile_x
        data = self.image["background"][index].sprite.data
        return int((data[y % 8][x % 8] % 4) > 0)

    def render_background(self):
        print(len(self.image["background"]))
        for i, tile in enumerate(self.image["background"]):
            x = (i % 32) * 8
            y = int(i / 32) * 8
            self.render_tile(tile, x, y, self.image["palette"])

        # Path("hoge.txt").unlink()
        # with Path("hoge.txt").open("a") as f:
        #     for y in range(0, H_SIZE):
        #         for x in range(0, V_SIZE):
        #             log = f"{x} {y} {self.data[y][x]} {id(self.data[y][x])}\n"
        #             f.write(log)

    def render_tile(self, tile, tile_x, tile_y, palette):
        offset_x = tile.scroll_x % 8
        offset_y = tile.scroll_y % 8

        for i in range(0, 8):
            for j in range(0, 8):
                palette_index = tile.palette_id * 4 + tile.sprite.data[i][j]
                color_id = palette[palette_index]
                x = tile_x + j - offset_x
                y = tile_y + i - offset_y
                if tile_x <= x < tile_x + 8 and tile_y <= y < tile_y + 8:
                    self.data[y][x] = COLORS[color_id]
                else:
                    print(f"{tile_x} <= {x} < {tile_x + 7} and {tile_y} <= {y} < {tile_y + 7}")
                    raise NotImplementedError

    def render_sprites(self):
        for sprite in self.image["sprites"]:
            self.render_sprite(sprite)

    # write on background(tile), 8*8
    def render_sprite(self, sprite):
        palette = self.image["palette"]

        is_vertical_reverse = bool(sprite.attr & 0x80)
        is_horizontal_reverse =  bool(sprite.attr & 0x40)
        is_low_priority =  bool(sprite.attr & 0x20)
        palette_id = sprite.attr & 0x03

        for i in range(0, 8):
            for j in range(0, 8):
                x = sprite.x + (7 - j) if is_horizontal_reverse else j
                y = sprite.y + (7 - i) if is_vertical_reverse else i
                if is_low_priority and self.should_pixel_hide(x, y):
                    continue

                if sprite.data[i][j]:
                    color_id = palette[palette_id * 4 + sprite.data[i][j] + 0x10]
                    self.data = COLORS[color_id]