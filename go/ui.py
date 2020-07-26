# -*- coding: utf-8 -*-

import asyncio
import concurrent.futures
from enum import Enum, auto
from typing import Optional

import pygame
import pygame.gfxdraw
from pygame.locals import (
    K_F4,
    KEYDOWN,
    KMOD_ALT,
    KMOD_CTRL,
    MOUSEBUTTONDOWN,
    MOUSEMOTION,
    QUIT,
    SRCALPHA,
    VIDEORESIZE,
)

from .models import Color, GameState, Position, Ring, Stone

DEFAULT_SQUARE_WIDTH = 50
LINE_WIDTH = 2
BOARD_COLOR = (220, 181, 121)
DEFAULT_COLORS = {
    Color.BLACK: (0, 0, 0),
    Color.WHITE: (255, 255, 255),
}
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


class EventType(Enum):
    PLACE_STONE = auto()


class Event:
    def __init__(self, type_: EventType, **attrs):
        self.type = type_

        if type_ == EventType.PLACE_STONE:
            self.pos = attrs["pos"]


class UI:
    def __init__(self, game_state: GameState):
        self.game_state = game_state

        self.display_size = 2 * (DEFAULT_SQUARE_WIDTH * self.game_state.board_size,)
        self._calculate_geometry()

        self.highlight: Optional[Ring] = None  # Indicates whose turn it is

        self._outgoing_event_q = asyncio.Queue()
        self._loop = asyncio.get_running_loop()
        self._pool = concurrent.futures.ThreadPoolExecutor()

    async def mouse_handler(self, e):
        pos = Position(
            *[
                (coord - padding) // self.square_width
                for coord, padding in zip(e.pos, self.display_padding)
            ]
        )
        if (0, 0) <= pos <= 2 * (
            self.game_state.board_size - 1,
        ) and pos not in self.game_state.stones:
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                await self._send(EventType.PLACE_STONE, pos=pos)
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

        board_surface = pygame.Surface(2 * (self.board_width,), flags=SRCALPHA)
        for x in range(self.game_state.board_size):  # Draws lines
            start = (
                int((x + 0.5) * self.square_width),
                self.square_width // 2,
            )
            end = (
                int((x + 0.5) * self.square_width),
                self.board_width - self.square_width // 2,
            )
            pygame.draw.line(board_surface, FG_COLOR, start, end, LINE_WIDTH)
        for y in range(self.game_state.board_size):
            start = (
                self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            end = (
                self.board_width - self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            pygame.draw.line(board_surface, FG_COLOR, start, end, LINE_WIDTH)

        # Draws hoshi positions
        for x, y in HOSHI_POSITIONS[self.game_state.board_size]:
            for f in (pygame.gfxdraw.aacircle, pygame.gfxdraw.filled_circle):
                f(
                    board_surface,
                    int((x + 0.5) * self.square_width),
                    int((y + 0.5) * self.square_width),
                    self.hoshi_radius,
                    FG_COLOR,
                )

        self.display.blit(board_surface, self.display_padding)

    def _get_ring_draw_options(self, ring: Ring):
        return (
            self.display,
            int((ring.pos.x + 0.5) * self.square_width) + self.display_padding[0],
            int((ring.pos.y + 0.5) * self.square_width) + self.display_padding[1],
            self.stone_radius,
            DEFAULT_COLORS[ring.color],
        )

    def _draw_ring(self, ring: Ring):
        pygame.gfxdraw.aacircle(*self._get_ring_draw_options(ring))

    def _draw_stone(self, stone: Stone):
        self._draw_ring(stone)
        pygame.gfxdraw.filled_circle(*self._get_ring_draw_options(stone))

    def _calculate_geometry(self):
        self.square_width = min(self.display_size) // self.game_state.board_size
        self.board_width = self.square_width * self.game_state.board_size
        self.hoshi_radius = int(HOSHI_RADIUS_SCALE * self.square_width)
        self.stone_radius = int(STONE_RADIUS_SCALE * self.square_width)
        self.display_padding = tuple(
            (x - self.board_width) // 2 for x in self.display_size
        )

    def _resize(self, size):
        self.display_size = size
        self.display = pygame.display.set_mode(size, pygame.RESIZABLE)
        self._calculate_geometry()

    async def _send(self, event_type, **attrs):
        event = Event(event_type, **attrs)
        await self._outgoing_event_q.put(event)

    async def render(self):
        self._draw_board()
        for stone in self.game_state.stones.values():
            self._draw_stone(stone)
        if self.highlight is not None:
            self._draw_ring(self.highlight)

        await self._loop.run_in_executor(self._pool, pygame.display.update)

    async def run(self):
        pygame.init()
        pygame.display.set_caption("Go")
        pygame.key.set_repeat(KEY_REPEAT_DELAY, KEY_REPEAT_INTERVAL)

        self.display = pygame.display.set_mode(self.display_size)

        running = True
        while running:
            for e in pygame.event.get():
                if e.type == QUIT:
                    running = False
                    break
                elif e.type == KEYDOWN:
                    ctrl, alt = (
                        pygame.key.get_mods() & key for key in (KMOD_CTRL, KMOD_ALT)
                    )
                    if e.key == K_F4 and alt:
                        running = False
                        break
                elif e.type in (MOUSEMOTION, MOUSEBUTTONDOWN):
                    await self.mouse_handler(e)
                elif e.type == VIDEORESIZE:
                    self._resize(e.size)
            if running:
                await self._outgoing_event_q.join()
                await self.render()

        pygame.quit()
