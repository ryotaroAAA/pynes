from logging import raiseExceptions
from pynes import *
import pygame
from pygame.locals import *
logger = PynesLogger.get_logger(__name__)

class Video:
    def __init__(self):
        pygame.init()
        self.surface = pygame.display.set_mode((V_SIZE, H_SIZE))
        pygame.display.set_caption("pynes")
        self.pixel = pygame.PixelArray(self.surface)

    def update(self, data):
        self.surface.fill((100, 100, 100))
        try:
            for y in range(0, H_SIZE):
                for x in range(0, V_SIZE):
                    self.pixel[x][y] = int(data[y][x])

        except:
            print("error", x, y, data[y][x], type(data[y][x]))
            raise NotImplementedError

        pygame.display.update()
        # for event in pygame.event.get():
        #     if event.type == QUIT:
        #         pygame.quit()
        #         sys.exit()