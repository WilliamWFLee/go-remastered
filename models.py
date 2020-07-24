# -*- coding: utf-8 -*-

from collections import namedtuple
from enum import Enum
from typing import Dict, List, Optional, Set

DEFAULT_BOARD_SIZE = 19


class Color(Enum):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


PositionBase = namedtuple("PositionBase", "x y")


class Position(PositionBase):
    def __lt__(self, other):
        if isinstance(other, type(self)):
            return not (self.x > other.x or self.y > other.y)
        elif isinstance(other, tuple):
            return not (self.x > other[0] or self.y > other[1])
        return NotImplemented

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        if isinstance(other, type(self)):
            return not (self.x < other.x or self.y < other.y)
        elif isinstance(other, tuple):
            return not (self.x < other[0] or self.y < other[1])
        return NotImplemented

    def __ge__(self, other):
        return self > other or self == other

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, tuple):
            return self.x == other[0] and self.y == other[1]
        return NotImplemented

    def __ne__(self, other):
        return not self == other

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


class Ring:
    def __init__(self, pos: Position, color: Color):
        self.pos = pos
        self.color = color

    def __repr__(self):
        return f"Ring(pos={self.pos}, color={self.color})"

    def __str__(self):
        return (
            f"<{type(self).__name__}, color {self.color.name} at {self.pos}>"
        )


class Stone(Ring):
    def __init__(self, pos: Position, color: Color):
        super().__init__(pos, color)
        self.group = Group(color, self)
        self.liberties = {direction: True for direction in Direction}

    @property
    def is_free(self):
        return any(self.liberties.values())

    def __repr__(self):
        return (
            f"{type(self).__name__}(pos={self.pos}, color={self.color}, "
            f"group={self.group!r}, liberties={self.liberties})"
        )

    def __str__(self):
        return f"{type(self).__name__} at {self.pos!r}>"


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
        return iter(self.stones[:])

    def __repr__(self):
        return f"Group(color={self.color}, stones={self.stones})"

    def __str__(self):
        return f"Group of {len(self.stones)} stones of color {self.color.name}"


HistoryEntry = namedtuple("HistoryEntry", "pos captures")


class GameState:
    """
    Class for representing a game of Go
    """

    def __init__(self, board_size: Optional[int] = None):
        # Game state
        self.current_color = Color.BLACK
        self.stones: Dict[Position, Stone] = {}
        self.history = []
        self.history_position = 0
        self.board_size = (
            board_size if board_size is not None else DEFAULT_BOARD_SIZE
        )

    @property
    def groups(self) -> Dict[Color, Set[Group]]:
        groups = {color: set() for color in Color}
        for stone in self.stones.values():
            groups[stone.color].add(stone.group)

        return groups

    def toggle_color(self):
        self.current_color = (
            Color.WHITE if self.current_color == Color.BLACK else Color.BLACK
        )

    def place_stone(self, pos, *, redo=False):
        new_stone = Stone(pos, self.current_color)
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
        captures = self.perform_captures()
        self.toggle_color()

        if not redo:
            # Truncates history for undos
            self.history = self.history[: self.history_position]
            # Stores position and captures made
            # Color is not stored, because it alternates, starting with black
            self.history += [HistoryEntry(pos, captures)]

        self.history_position += 1

    def remove_stone(self, pos):
        stone = self.stones[pos]
        del self.stones[pos]
        stone.group.stones.remove(stone)

    def perform_captures(self):
        captures = {color: [] for color in Color}
        for color in (
            Color.WHITE if self.current_color == Color.BLACK else Color.BLACK,
            self.current_color,
        ):
            self.update_liberties()
            for group in self.groups[color]:
                if group.can_capture:
                    for stone in group:
                        self.remove_stone(stone.pos)
                        captures[stone.color] += [stone.pos]

        return {
            color: tuple(captures[color]) if captures[color] else None
            for color in Color
        }

    def update_liberties(self):
        for stone in self.stones.values():
            for direction in Direction:
                adj_pos = stone.pos + direction.value
                if (0, 0) <= adj_pos <= 2 * (
                    self.board_size - 1,
                ) and adj_pos not in self.stones:
                    stone.liberties[direction] = True
                else:
                    stone.liberties[direction] = False

    def undo(self):
        if self.history_position > 0:
            self.history_position -= 1

            history_entry = self.history[self.history_position]
            for color, positions in history_entry.captures.items():
                if positions is not None:
                    for pos in positions:
                        new_stone = Stone(pos, color)
                        self.stones[pos] = new_stone

            self.remove_stone(history_entry.pos)
            self.toggle_color()

    def redo(self):
        if self.history_position < len(self.history):
            self.place_stone(
                self.history[self.history_position].pos, redo=True
            )
