# -*- coding: utf-8 -*-

from collections import namedtuple
from enum import Enum
from functools import total_ordering
from typing import Dict, List, Sequence, Set

import pygame
import pygame.gfxdraw
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, QUIT

LINE_WIDTH = 2
BOARD_COLOR = (220, 181, 121)
DEFAULT_BOARD_SIZE = 19
DEFAULT_SQUARE_WIDTH = 50
DEFAULT_COLORS = [
    (0, 0, 0),
    (255, 255, 255),
]
FG_COLOR = (0, 0, 0)
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
    def update(self, display):
        raise NotImplementedError


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


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

    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)(self.x + other.x, self.y + other.y)
        elif isinstance(other, tuple):
            return type(self)(self.x + other[0], self.y + other[1])
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __hash__(self):
        return super().__hash__()


class Ring(Graphic):
    def __init__(
        self, pos: Position, color: Color, square_width: int, radius: int
    ):
        self.pos = pos
        self.color = color
        self.square_width = square_width
        self.radius = radius

    @property
    def _draw_options(self):
        return (
            int((self.pos.x + 0.5) * self.square_width),
            int((self.pos.y + 0.5) * self.square_width),
            self.radius,
            self.color.value,
        )

    def update(self, display):
        pygame.gfxdraw.aacircle(display, *self._draw_options)


class Stone(Ring):
    def __init__(
        self, pos: Position, color: Color, square_width: int, radius: int
    ):
        super().__init__(pos, color, square_width, radius)
        self.group = Group(color, self)
        self.liberties = {direction: True for direction in Direction}

    def update(self, display):
        super().update(display)
        pygame.gfxdraw.filled_circle(display, *self._draw_options)

    @property
    def is_free(self):
        return any(self.liberties.values())


class Group:
    def __init__(self, color: Color, *stones: Stone):
        self.color = color
        self.stones = list(stones)

    @property
    def can_capture(self):
        return all(not stone.is_free for stone in self.stones)

    @classmethod
    def merge(cls, groups: List["Group"]):
        if len(groups) == 1:
            return groups[0]

        color = groups[0].color
        new_group = cls(color)
        for group in groups:
            for stone in group:
                new_group.stones += [stone]
                stone.group = new_group

        return new_group

    def __iter__(self):
        return iter(self.stones)


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
        self.stones: Dict[Position, Stone] = {}
        self.highlight = None  # Indicates whose turn it is

    @property
    def groups(self) -> Dict[Color, Set[Group]]:
        groups = {}
        for color in Color:
            groups[color] = set()
            for stone in self.stones.values():
                groups[color].add(stone.group)

        return groups

    def draw_board(self):
        self.display.fill(BOARD_COLOR)  # Set board color
        for x in range(self.board_size):  # Draws lines
            start = (
                int((x + 0.5) * self.square_width),
                self.square_width // 2,
            )
            end = (
                int((x + 0.5) * self.square_width),
                self.board_width - self.square_width // 2,
            )
            pygame.draw.line(self.display, FG_COLOR, start, end, LINE_WIDTH)
        for y in range(self.board_size):
            start = (
                self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            end = (
                self.board_width - self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            pygame.draw.line(self.display, FG_COLOR, start, end, LINE_WIDTH)

        # Draws hoshi positions
        for x, y in HOSHI_POSITIONS[self.board_size]:
            for f in (pygame.gfxdraw.filled_circle, pygame.gfxdraw.aacircle):
                f(
                    self.display,
                    int((x + 0.5) * self.square_width),
                    int((y + 0.5) * self.square_width),
                    self.hoshi_radius,
                    FG_COLOR,
                )

    def toggle_color(self):
        self.current_color = (
            Color.WHITE if self.current_color == Color.BLACK else Color.BLACK
        )

    def place_stone(self, pos):
        new_stone = Stone(
            pos, self.current_color, self.square_width, self.stone_radius
        )
        self.stones[pos] = new_stone
        merge_groups = [new_stone.group]
        for direction in Direction:
            adj_pos = new_stone.pos + direction.value
            if (
                adj_pos in self.stones
                and self.stones[adj_pos].color == new_stone.color
            ):
                merge_groups += [self.stones[adj_pos].group]

        Group.merge(merge_groups)

        self.update_liberties()
        self.perform_captures()
        self.toggle_color()

    def perform_captures(self):
        for color in (
            self.current_color,
            Color.WHITE if self.current_color == Color.BLACK else Color.BLACK,
        ):
            for group in self.groups[color]:
                if group.can_capture:
                    for stone in group:
                        del self.stones[stone.pos]

    def update_liberties(self):
        for stone in self.stones.values():
            for direction in Direction:
                adj_pos = stone.pos + direction.value
                if (0, 0) <= adj_pos <= 2 * (
                    self.board_size,
                ) and adj_pos not in self.stones:
                    stone.liberties[direction] = True
                else:
                    stone.liberties[direction] = False

    def click(self, pos):
        if pos <= 2 * (self.board_size,) and pos not in self.stones:
            self.place_stone(pos)

    def render(self):
        self.draw_board()
        for stone in self.stones.values():
            stone.update(self.display)
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
                elif e.type in (MOUSEMOTION, MOUSEBUTTONDOWN):
                    pos = Position.from_tuple(e.pos, self.square_width)
                    if e.type == MOUSEBUTTONDOWN:
                        self.click(pos)
            if running:
                self.render()
