# -*- coding: utf-8 -*-

from enum import Enum

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


class Color(Enum):
    BLACK = 0
    WHITE = 1


class Go:
    """
    Class for representing a game of Go
    """

    def __init__(self, board_size: int = None, square_width: int = None):
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

        self.current_color = Color.BLACK
        self.history = []
        self.history_position = 0
