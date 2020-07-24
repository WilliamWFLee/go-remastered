# -*- coding: utf-8 -*-

from typing import Optional

import pygame
import pygame.gfxdraw
from pygame.locals import (
    K_F4,
    KEYDOWN,
    KMOD_ALT,
    KMOD_CTRL,
    KMOD_SHIFT,
    MOUSEBUTTONDOWN,
    MOUSEMOTION,
    QUIT,
    K_y,
    K_z,
)

from models import GameState, Position, Ring, Stone

LINE_WIDTH = 2
BOARD_COLOR = (220, 181, 121)
DEFAULT_SQUARE_WIDTH = 50
DEFAULT_COLORS = [
    (0, 0, 0),
    (255, 255, 255),
]
FG_COLOR = (0, 0, 0)
KEY_REPEAT_DELAY = 500
KEY_REPEAT_INTERVAL = 50
BOARD_SIZES = (9, 13, 19)
HOSHI_POSITIONS = {
    9: [(x, y) for x in (2, 6) for y in (2, 6)] + [(4, 4)],
    13: [(x, y) for x in (3, 6, 9) for y in (3, 6, 9)],
    19: [(x, y) for x in (3, 9, 15) for y in (3, 9, 15)],
}

HOSHI_RADIUS_SCALE = 0.08
STONE_RADIUS_SCALE = 0.46


class Graphic:
    def update(self, display):
        raise NotImplementedError


class UI:
    def __init__(
        self, game_state: GameState, square_width: Optional[int] = None,
    ):
        self.game_state = game_state
        # Game dimensions
        self.square_width = (
            square_width if square_width is not None else DEFAULT_SQUARE_WIDTH
        )

        self.hoshi_radius = int(HOSHI_RADIUS_SCALE * self.square_width)
        self.stone_radius = int(STONE_RADIUS_SCALE * self.square_width)
        self.board_width = self.game_state.board_size * self.square_width

        self.screen_dimensions = 2 * (self.board_width,)
        self.highlight: Optional[Ring] = None  # Indicates whose turn it is

    def mouse_handler(self, e):
        pos = Position(*[coord // self.square_width for coord in e.pos])
        if (0, 0) <= pos <= 2 * (
            self.game_state.board_size - 1,
        ) and pos not in self.game_state.stones:
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                self.game_state.place_stone(pos)
            elif e.type == MOUSEMOTION:
                if self.highlight:
                    self.highlight.pos = pos
                    self.highlight.color = self.game_state.current_color
                else:
                    self.highlight = Ring(pos, self.game_state.current_color)
        elif e.type == MOUSEMOTION:
            self.highlight = None

    def _draw_board(self):
        self.display.fill(BOARD_COLOR)  # Set board color
        for x in range(self.game_state.board_size):  # Draws lines
            start = (
                int((x + 0.5) * self.square_width),
                self.square_width // 2,
            )
            end = (
                int((x + 0.5) * self.square_width),
                self.board_width - self.square_width // 2,
            )
            pygame.draw.line(self.display, FG_COLOR, start, end, LINE_WIDTH)
        for y in range(self.game_state.board_size):
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
        for x, y in HOSHI_POSITIONS[self.game_state.board_size]:
            for f in (pygame.gfxdraw.filled_circle, pygame.gfxdraw.aacircle):
                f(
                    self.display,
                    int((x + 0.5) * self.square_width),
                    int((y + 0.5) * self.square_width),
                    self.hoshi_radius,
                    FG_COLOR,
                )

    def _get_ring_draw_options(self, ring: Ring):
        return (
            self.display,
            int((ring.pos.x + 0.5) * self.square_width),
            int((ring.pos.y + 0.5) * self.square_width),
            self.stone_radius,
            ring.color.value,
        )

    def _draw_ring(self, ring: Ring):
        pygame.gfxdraw.aacircle(*self._get_ring_draw_options(ring))

    def _draw_stone(self, stone: Stone):
        self._draw_ring(stone)
        pygame.gfxdraw.filled_circle(*self._get_ring_draw_options(stone))

    def render(self):
        self._draw_board()
        for stone in self.game_state.stones.values():
            self._draw_stone(stone)
        if self.highlight is not None:
            self._draw_ring(self.highlight)
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
                    running = False
                    break
                elif e.type == KEYDOWN:
                    ctrl, shift, alt = (
                        pygame.key.get_mods() & key
                        for key in (KMOD_CTRL, KMOD_SHIFT, KMOD_ALT)
                    )
                    if e.key == K_F4 and alt:
                        running = False
                        break
                    if ctrl:
                        if e.key == K_y:
                            self.game_state.redo()
                        if e.key == K_z:
                            if shift:
                                self.game_state.redo()
                            else:
                                self.game_state.undo()
                elif e.type in (MOUSEMOTION, MOUSEBUTTONDOWN):
                    self.mouse_handler(e)
            if running:
                self.render()

        pygame.quit()
