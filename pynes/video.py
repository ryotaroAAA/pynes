from logging import raiseExceptions
from pynes import *
import pygame
from pygame.locals import *
logger = PynesLogger.get_logger(__name__)

PAD_DELAY = 10
PAD_INTERVAL = 10
class Video:
    def __init__(self, cpu):
        pygame.init()

        self.cpu = cpu
        self.surface = pygame.display.set_mode((H_SIZE, V_SIZE))

        pygame.display.set_caption("pynes")
        self.pixel = pygame.PixelArray(self.surface)

        # get pad input every 1 frame (60fps)
        pygame.key.set_repeat(PAD_DELAY, PAD_INTERVAL)

    def update(self, data):
        self.surface.fill((0, 0, 0))
        try:
            for x in range(0, H_SIZE):
                for y in range(0, V_SIZE):
                    self.pixel[x][y] = int(data[y][x])

        except:
            print("error", x, y, data[y][x], type(data[y][x]))
            raise NotImplementedError

        pygame.display.update()
        for event in pygame.event.get():
            # print(vars(event))
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if (event.key == K_ESCAPE or
                        event.key == K_q):
                    # quit
                    print("EXIT!")
                    pygame.quit()
                    sys.exit()
                elif event.key == K_a:
                    # A
                    # print("A")
                    self.cpu.pad1.A = True
                elif event.key == K_s:
                    # B
                    # print("B")
                    self.cpu.pad1.B = True
                elif event.key == K_d:
                    # start
                    # print("start")
                    self.cpu.pad1.STA = True
                elif event.key == K_f:
                    # select
                    # print("select")
                    self.cpu.pad1.SEL = True
                elif event.key == K_LEFT:
                    # cursor left
                    # print("left")
                    self.cpu.pad1.LEFT = True
                elif event.key == K_RIGHT:
                    # cursor right
                    # print("right")
                    self.cpu.pad1.RIGHT = True
                elif event.key == K_UP:
                    # cursor up
                    # print("up")
                    self.cpu.pad1.UP = True
                elif event.key == K_DOWN:
                    # cursor down
                    # print("down")
                    self.cpu.pad1.DOWN = True
                # print(self.cpu.pad1)