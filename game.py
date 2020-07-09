# -*- coding: utf-8 -*-

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
