# -*- coding: utf-8 -*-

from collections import namedtuple
from enum import Enum
from functools import total_ordering
from typing import Sequence

import pygame
import pygame.gfxdraw
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, QUIT

LINE_WIDTH = 2
BOARD_COLOUR = (220, 181, 121)
DEFAULT_BOARD_SIZE = 19
DEFAULT_SQUARE_WIDTH = 50
DEFAULT_COLOURS = [
    (0, 0, 0),
    (255, 255, 255),
]
FG_COLOUR = (0, 0, 0)
KEY_REPEAT_DELAY = 300
KEY_REPEAT_INTERVAL = 5
BOARD_SIZES = (9, 13, 19)
HOSHI_POSITIONS = {
    9: [(x, y) for x in (2, 6) for y in (2, 6)] + [(4, 4)],
    13: [(x, y) for x in (3, 6, 9) for y in (3, 6, 9)],
    19: [(x, y) for x in (3, 9, 15) for y in (3, 9, 15)],
}

HOSHI_RADIUS_SCALE = 0.08
STONE_RADIUS_SCALE = 0.46
STAT_PANEL_WIDTH_SCALE = 8
STAT_SCALE = {
    "width": 0.5,
    "height": 0.9,
}


class Graphic:
    def update(self):
        raise NotImplementedError


class Color(Enum):
    BLACK = 0
    WHITE = 1


PositionBase = namedtuple("PositionBase", "x y")


@total_ordering
class Position(PositionBase):
    @classmethod
    def from_mouse_pos(cls, x: int, y: int, square_width: int):
        return cls(x // square_width, y // square_width)

    @classmethod
    def from_tuple(cls, pos: Sequence[int], square_width: int):
        return cls.from_mouse_pos(*pos, square_width)

    def __lt__(self, other):
        if isinstance(other, type(self)):
            return self.x < other.x or self.y < other.y
        elif isinstance(other, tuple):
            return self.x < other[0] or self.y < other[1]
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, tuple):
            return self.x == other[0] and self.y == other[1]
        return NotImplemented


class Go:
    """
    Class for representing a game of Go
    """

    def __init__(self, board_size: int = None, square_width: int = None):
        # Game dimensions
        self.board_size = (
            board_size if board_size is not None else DEFAULT_BOARD_SIZE
        )
        self.square_width = (
            square_width if square_width is not None else DEFAULT_SQUARE_WIDTH
        )

        self.hoshi_radius = int(HOSHI_RADIUS_SCALE * self.square_width)
        self.stone_radius = int(STONE_RADIUS_SCALE * self.square_width)
        self.board_width = self.board_size * self.square_width

        self.stat_panel_width = STAT_PANEL_WIDTH_SCALE * self.square_width
        self.stat_height = int(STAT_SCALE["height"] * self.square_width)
        self.stat_width = int(STAT_SCALE["width"] * self.stat_panel_width)
        self.screen_dimensions = (
            self.board_width + self.stat_panel_width + self.square_width // 2,
            self.board_width,
        )

        # Game state
        self.current_color = Color.BLACK

    def draw_board(self):
        self.display.fill(BOARD_COLOUR)  # Set board colour
        for x in range(self.board_size):  # Draws lines
            start = (
                int((x + 0.5) * self.square_width),
                self.square_width // 2,
            )
            end = (
                int((x + 0.5) * self.square_width),
                self.board_width - self.square_width // 2,
            )
            pygame.draw.line(self.display, FG_COLOUR, start, end, LINE_WIDTH)
        for y in range(self.board_size):
            start = (
                self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            end = (
                self.board_width - self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            pygame.draw.line(self.display, FG_COLOUR, start, end, LINE_WIDTH)

        # Draws hoshi positions
        for x, y in HOSHI_POSITIONS[self.board_size]:
            for f in (pygame.gfxdraw.filled_circle, pygame.gfxdraw.aacircle):
                f(
                    self.display,
                    int((x + 0.5) * self.square_width),
                    int((y + 0.5) * self.square_width),
                    self.hoshi_radius,
                    FG_COLOUR,
                )

    def render(self):
        self.draw_board()
        pygame.display.update()

    def run(self):
        pygame.init()
        pygame.display.set_caption("Go")
        pygame.key.set_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)

        self.display = pygame.display.set_mode(self.screen_dimensions)

        running = True
        while running:
            for e in pygame.event.get():
                if e.type == QUIT:
                    pygame.quit()
                    running = False
                    break
            if running:
                self.render()
