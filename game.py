import json
import os
import random
import sys

import pygame
import pygame.gfxdraw
from pygame.locals import (  # pylint: disable=no-name-in-module
    QUIT,
    KEYDOWN,
    MOUSEMOTION,
    MOUSEBUTTONDOWN,
    KMOD_CTRL,
    KMOD_ALT,
    KMOD_SHIFT,
    K_F4,
    K_o,
    K_r,
    K_s,
    K_y,
    K_z,
)


class Graphic:
    graphics = []

    @staticmethod
    def update_all():
        for graphic in Graphic.graphics:
            graphic.update()

    def __init__(self):
        self.graphics.append(self)


class Stone(Graphic):  # PORT NUMBER: 7179
    stones = {}

    def __init__(self, app, coords, player, undo=False, redo=False):
        super().__init__()
        self.coords = coords  # (x,y) tuple or list
        self.app = app
        self.stones[coords] = self
        self.player = player
        self.group = None
        self.liberties = {
            (1, 0): True,  # Top
            (0, 1): True,  # Right
            (-1, 0): True,  # Left
            (0, -1): True,  # Bottom
        }
        if not undo:
            new_history_entry = [self.coords]

        merger_groups = []  # Groups to merge

        x, y = self.coords
        for x_incr, y_incr in self.liberties:
            if (
                0 <= x + x_incr < self.app.board_size
                and 0 <= y + y_incr < self.app.board_size
                and (x + x_incr, y + y_incr) in self.stones
            ):
                adj_stone = Stone.stones[(x + x_incr, y + y_incr)]
                if adj_stone.player == self.player and adj_stone.group:
                    if not adj_stone.group in merger_groups:
                        merger_groups.append(adj_stone.group)
        if len(merger_groups) > 0:
            self.group = merger_groups[0]
            self.group.add_stone(self)
        if not self.group:
            new_group = Group(self.app, self.player)
            new_group.add_stone(self)
            self.group = new_group
        if len(merger_groups) > 1:
            self.group.merge(*merger_groups[1:])
        if not undo:
            removals = Group.evaluate_all_liberties(self.app.current_player)
        else:
            if player == self.app.current_player:
                Stat.stats[not self.app.current_player]["captures"].value -= 1
            else:
                Stat.stats[player]["suicides"].value -= 1
        if not (undo or redo):
            if removals:
                new_history_entry += [removals]
            if self.app.history_position < len(self.app.history):
                self.app.history = self.app.history[
                    : self.app.history_position
                ]
            self.app.history.append(new_history_entry)
            self.app.history_position += 1

    def __repr__(self):
        return "<Stone at " + str(self.coords) + ">"

    def update(self):
        x, y = self.coords
        options = [
            self.app.display,
            int((x + 0.5) * self.app.square_width),
            int((y + 0.5) * self.app.square_width),
            self.app.stone_radius,
            self.app.colours[self.player],
        ]
        for f in [pygame.gfxdraw.aacircle, pygame.gfxdraw.filled_circle]:
            f(*options)

    def capture(self):
        Graphic.graphics.remove(self)
        del Stone.stones[self.coords]
        self.group.remove_stone(self)
        if self.player == self.app.current_player:
            Stat.stats[self.player]["suicides"].value += 1
        else:
            Stat.stats[not self.player]["captures"].value += 1

    def undo_claim(self):
        Graphic.graphics.remove(self)
        del Stone.stones[self.coords]
        self.group.undo_stone(self)

    def evaluate_liberty(self):
        x, y = self.coords
        for x_incr, y_incr in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if (
                0 <= x + x_incr < self.app.board_size
                and 0 <= y + y_incr < self.app.board_size
            ):
                adj_stone = (x + x_incr, y + y_incr)
                self.liberties[(x_incr, y_incr)] = (
                    False if adj_stone in Stone.stones else True
                )
            else:
                self.liberties[(x_incr, y_incr)] = False

        return [self.liberties[key] for key in self.liberties]


class Group:
    groups = [[], []]

    def __init__(self, app, player=None):
        self.player = player
        self.app = app
        self.stones = []
        self.groups[player].append(self)

    def __repr__(self):
        return (
            "<Group at "
            + ", ".join(str(stone.coords) for stone in self.stones)
            + ">"
        )

    @classmethod
    def evaluate_all_liberties(cls, player):
        removals = []
        for stone_player in [not player, player]:
            for group in cls.groups[stone_player][:]:
                captures = group.evaluate_liberties()
                if captures:
                    removals += captures
                    for capture in captures:
                        Stone.stones[capture[0]].capture()

        return removals

    def add_stone(self, *stones):
        for stone in stones:
            self.stones.append(stone)

    def remove_stone(self, *stones):
        for stone in stones:
            self.stones.remove(stone)
            stone.group = None
        if len(self.stones) == 0:
            Group.groups[self.player].remove(self)

    def capture_stone(self, *stones):
        self.remove_stone(*stones)

    def undo_stone(self, *stones):
        self.remove_stone(*stones)
        if len(self.stones) > 0:
            oldStones = self.stones[1:]
            for stone in oldStones:
                self.remove_stone(stone)
            for stone in oldStones:
                merger_groups = []
                x, y = stone.coords
                for x_incr, y_incr in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    if (
                        0 <= x + x_incr < self.app.board_size
                        and 0 <= y + y_incr < self.app.board_size
                        and (x + x_incr, y + y_incr) in Stone.stones
                    ):
                        adj_stone = Stone.stones[(x + x_incr, y + y_incr)]
                        if (
                            adj_stone.player == stone.player
                            and adj_stone.group
                        ):
                            if not adj_stone.group in merger_groups:
                                merger_groups.append(adj_stone.group)
                if len(merger_groups) > 0:
                    stone.group = merger_groups[0]
                    stone.group.add_stone(stone)
                if not stone.group:
                    new_group = Group(self.app, stone.player)
                    new_group.add_stone(stone)
                    stone.group = new_group
                if len(merger_groups) > 1:
                    stone.group.merge(*merger_groups[1:])

    def merge(self, *groups):
        for group in groups[:]:
            self.stones += group.stones
            for stone in group.stones:
                stone.group = self
            self.groups[self.player].remove(group)

    def evaluate_liberties(self):
        liberties = []
        removals = []
        for stone in self.stones:
            liberties += stone.evaluate_liberty()

        if not any(liberties):
            for stone in self.stones:
                removals.append((stone.coords, stone.player))

        return removals if removals else None


class TextLabel(Graphic):
    texts = [[], []]

    def __init__(
        self, app, player, row, label, text, bold=False, italic=False
    ):
        super().__init__()
        self.app = app
        self.player = player
        self.row = row
        self.label = label
        self.text = text.title()
        self.texts[self.player].append(self)

        fontSize = int(3 * self.app.square_width / 5)
        self.font = pygame.font.SysFont("Calibri", fontSize, bold, italic)


class Heading(TextLabel):
    def update(self):
        text = (
            (self.text + " <")
            if self.app.current_player == self.player
            else self.text
        )
        _, text_height = self.font.size(text)
        text_surface = self.font.render(
            text, True, self.app.colours[self.player]
        )
        x = self.app.board_width + self.app.stat_width * self.player
        y = (
            int((self.row + 0.5) * self.app.stat_height)
            - text_height // 2
            + self.app.square_width // 2
        )
        self.app.display.blit(text_surface, (x, y))


class Stat(TextLabel):
    stats = [{}, {}]

    def __init__(
        self, app, player, row, label, text, value, bold=False, italic=False
    ):
        super().__init__(app, player, row, label, text, bold, italic)
        self.row = row + 1
        self.value = value
        self.stats[self.player][self.label] = self

    def __repr__(self):
        return f"<Stat {self.label} for {self.player}>"

    def update(self):
        text = f"{self.text.title()}: {self.value}"
        _, text_height = self.font.size(text)
        text_surface = self.font.render(
            text, True, self.app.colours[self.player]
        )
        x = self.app.board_width + (self.app.stat_width * self.player)
        y = (
            int((self.row + 0.5) * self.app.stat_height)
            - text_height // 2
            + self.app.square_width // 2
        )
        self.app.display.blit(text_surface, (x, y))


class StatButton(Graphic):
    buttons = {0: [], 1: []}

    def __init__(self, app, command, text, row, fg_colour, bg_colour):
        super().__init__()
        self.app = app
        self.command = command
        self.text = text.title()
        self.row = row  # Row count from bottom, start from 0
        self.fg_colour = fg_colour
        self.bg_colour = bg_colour
        self.font = pygame.font.SysFont(
            "Calibri", int(3 * self.app.square_width / 5)
        )
        self.hover = False
        self.buttons[row].append(self)
        self.calculate_geometry()

    @classmethod
    def collide_event(cls, e):
        for row in [0, 1]:
            for button in cls.buttons[row]:
                button.hover = False
                if button.button_rect.collidepoint(e.pos):
                    button.hover = True

    @classmethod
    def click_detect(cls, e):
        for row in [0, 1]:
            for button in cls.buttons[row]:
                if button.button_rect.collidepoint(e.pos):
                    button.command()

    def calculate_geometry(self):
        self.coords = (
            self.app.board_width
            + self.buttons[self.row].index(self)
            * self.app.stat_panel_width
            // len(self.buttons[self.row]),
            self.app.board_width
            - (self.row + 1) * self.app.stat_height
            - self.app.square_width // 2,
        )
        self.dimensions = (
            self.app.stat_panel_width // len(self.buttons[self.row]),
            self.app.stat_height,
        )
        self.button_rect = pygame.Rect(self.coords, self.dimensions)

    def update(self):
        self.calculate_geometry()
        pygame.draw.rect(self.app.display, self.bg_colour, self.button_rect)
        if self.hover:
            pygame.gfxdraw.rectangle(
                self.app.display, self.button_rect, self.fg_colour
            )
        text_width, text_height = self.font.size(self.text)
        text_surface = self.font.render(self.text, True, self.fg_colour)
        x, y = self.coords
        width, height = self.dimensions
        self.app.display.blit(
            text_surface,
            (x + (width - text_width) // 2, (y + (height - text_height) // 2)),
        )


class Highlight(Graphic):
    def __init__(self, app, coords):
        for graphic in Graphic.graphics:
            if isinstance(graphic, Highlight):
                Graphic.graphics.remove(graphic)
        super().__init__()
        self.coords = coords
        self.app = app

    def update(self):
        if not self.coords in Stone.stones:
            pygame.gfxdraw.aacircle(
                self.app.display,
                int((self.coords[0] + 0.5) * self.app.square_width),
                int((self.coords[1] + 0.5) * self.app.square_width),
                self.app.stone_radius,
                self.app.colours[self.app.current_player],
            )


class Application:
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

    def __init__(self):
        self.handicap_radius = int(2 * self.square_width / 25)
        self.stone_radius = int(23 * self.square_width / 50)
        self.board_width = self.board_size * self.square_width

        self.stat_panel_width = 8 * self.square_width
        self.stat_height = int(9 * self.square_width / 10)
        self.stat_width = self.stat_panel_width // 2
        self.screen_dimensions = (
            self.board_width + self.stat_panel_width + self.square_width // 2,
            self.board_width,
        )

        self.current_player = 0
        self.history = []  # Format: (Size, [(Stone object, list removals)*])
        self.history_position = 0

        pygame.init()  # pylint: disable=no-member
        pygame.display.set_caption("Go")
        pygame.key.set_repeat(self.KEY_REPEAT_DELAY, self.KEY_REPEAT_INTERVAL)

        self.display = pygame.display.set_mode(self.screen_dimensions)
        self.random = False
        self.make_stats()

    def claim(self, coords):
        x, y = coords
        if (
            0 <= x < self.board_size
            and 0 <= x < self.board_size
            and not (x, y) in Stone.stones
        ):
            Stone(self, (x, y), self.current_player)
            self.toggle_colour()

    def pass_turn(self, redo=False):
        Stat.stats[self.current_player]["passes"].value += 1

        if not redo:
            self.history = self.history[: self.history_position]
            self.history += [[None, self.current_player, []]]
            self.toggle_colour()
        self.history_position += 1

    def evaluate_territories(self):
        territories = [[], []]

        def check_adjacent_stones(stone, stones, empty_stones, territory):
            x, y = stone
            for x_incr, y_incr in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                if (adj_stone := (x + x_incr, y + y_incr)) in stones:
                    if adj_stone in empty_stones:
                        empty_stones.remove(adj_stone)
                        territory["stones"] += [adj_stone]
                        check_adjacent_stones(
                            adj_stone, stones, empty_stones, territory
                        )
                    if adj_stone in Stone.stones:
                        adj_stone = Stone.stones[adj_stone]
                        if (
                            territory["player"] is not None
                            and territory["player"] != adj_stone.player
                        ):
                            territory["dame"] = True
                        territory["player"] = adj_stone.player

        empty_stones = []
        stones = [
            (x, y)
            for x in range(self.board_size)
            for y in range(self.board_size)
        ]
        for stone in stones:
            if not stone in Stone.stones:
                empty_stones += [stone]

        while len(empty_stones):
            empty_stone = empty_stones[0]

            territory = {
                "stones": [],
                "player": None,
                "dame": False,
            }
            territory["stones"] += [empty_stone]

            empty_stones.remove(empty_stone)
            check_adjacent_stones(empty_stone, stones, empty_stones, territory)

            # print(territory["stones"])

            if (
                not territory["dame"]
                and len(territory["stones"]) < 0.5 * self.board_size ** 2
            ):
                territories[territory["player"]] += [
                    territory["stones"]
                ]  # pylint: disable=invalid-sequence-index

        for player in range(2):
            # print(territories[player], end="\n\n")
            Stat.stats[player]["territory"].value = sum(
                [len(territory) for territory in territories[player]]
            )

    def undo(self, loading=False):
        if self.history and self.history_position:
            self.history_position -= 1
            history_entry = self.history[self.history_position]
            if history_entry[0]:
                if len(history_entry) > 1:
                    for stone in history_entry[1]:
                        Stone(self, stone[0], stone[1], undo=True)
                self.toggle_colour()
                Stone.stones[history_entry[0]].undo_claim()
            else:
                self.toggle_colour()
                Stat.stats[self.current_player]["passes"].value -= 1
            if not loading:
                self.evaluate_territories()

    def redo(self):
        if len(self.history) > self.history_position >= 0:
            history_entry = self.history[self.history_position]

            if history_entry[0]:
                Stone(self, history_entry[0], self.current_player, False, True)
                self.history_position += 1
            else:
                self.pass_turn(True)

            self.toggle_colour()
            self.evaluate_territories()

    def save(self):
        def serialize(obj):
            if isinstance(obj, Stone):
                return obj.coords
            else:
                raise TypeError(
                    f"Object of type {type(obj)} " "is not serializable"
                )

        file = open("history.json", "w")
        save = {
            "size": self.board_size,
            "history": [entry[0] for entry in self.history],
        }
        json.dump(save, file, default=serialize, separators=(",", ":"))
        file.close()

    def load(self):
        for _ in range(len(self.history)):
            self.undo(True)
        file = open("history.json", "r")
        raw_history = json.load(file)
        if raw_history["size"] == self.board_size:
            for history_entry in raw_history["history"]:
                if history_entry:
                    self.claim(history_entry)
                else:
                    self.pass_turn()
        self.evaluate_territories()

    def toggle_colour(self):
        self.current_player = not self.current_player

    def randomise(self):
        empty_stones = [
            (x, y)
            for x in range(self.board_size)
            for y in range(self.board_size)
            if not (x, y) in Stone.stones
        ]
        x, y = random.choice(empty_stones)
        empty_stones.remove((x, y))
        Stone(self, (x, y), self.current_player)
        self.toggle_colour()

    def construct_board(self):

        self.display.fill(self.BOARD_COLOUR)  # Set board colour

        for x in range(self.board_size):  # Draws lines
            start = (
                int((x + 0.5) * self.square_width),
                self.square_width // 2,
            )
            end = (
                int((x + 0.5) * self.square_width),
                self.board_width - self.square_width // 2,
            )
            pygame.draw.line(
                self.display, self.FG_COLOUR, start, end, self.LINE_WIDTH
            )
        for y in range(self.board_size):
            start = (
                self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            end = (
                self.board_width - self.square_width // 2,
                int((y + 0.5) * self.square_width),
            )
            pygame.draw.line(
                self.display, self.FG_COLOUR, start, end, self.LINE_WIDTH
            )

        # Draws hoshi positions
        for x, y in self.HOSHI_POSITIONS[self.board_size]:
            for f in [pygame.gfxdraw.filled_circle, pygame.gfxdraw.aacircle]:
                f(
                    self.display,
                    int((x + 0.5) * self.square_width),
                    int((y + 0.5) * self.square_width),
                    self.handicap_radius,
                    self.FG_COLOUR,
                )

    def make_stats(self):
        for player in [0, 1]:
            Heading(
                self,
                player,
                0,
                str(player) + "Heading",
                "Player 1" if not player else "Player 2",
                True,
            )
            for row, (label, text, value) in enumerate(
                [
                    ("captures", "Captures", 0),
                    ("territory", "Territory", 0),
                    ("suicides", "Suicides", 0),
                    ("passes", "Passes", 0),
                ]
            ):
                Stat(self, player, row, label, text, value)

        for command, text, row in [
            (self.pass_turn, "pass", 0),
            (self.undo, "undo", 1),
            (self.redo, "redo", 1),
            (self.save, "save", 1),
            (self.load, "load", 1),
        ]:
            StatButton(
                self, command, text, row, self.FG_COLOUR, self.BOARD_COLOUR
            )

    def render(self):
        self.construct_board()
        Graphic.update_all()
        pygame.display.update()

    def run_game(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for e in pygame.event.get():
                if e.type == QUIT:
                    pygame.quit()  # pylint: disable=no-member
                    running = False
                    break
                elif e.type == KEYDOWN:
                    ctrl = pygame.key.get_mods() & KMOD_CTRL
                    alt = pygame.key.get_mods() & KMOD_ALT
                    shift = pygame.key.get_mods() & KMOD_SHIFT
                    if ctrl:
                        if e.key == K_z and not self.random:
                            if shift:
                                self.redo()
                            else:
                                self.undo()
                        elif e.key == K_y and not self.random:
                            self.redo()
                        elif e.key == K_s:
                            self.save()
                        elif e.key == K_o:
                            self.load()
                        elif e.key == K_r:
                            self.random = not self.random
                            if not self.random:
                                self.evaluate_territories()
                    elif e.key == K_F4 and alt:
                        pygame.quit()  # pylint: disable=no-member
                        running = False
                        break
                elif e.type in (MOUSEMOTION, MOUSEBUTTONDOWN):
                    x, y = e.pos
                    stone_x = x // self.square_width
                    stone_y = y // self.square_width

                    if e.type == MOUSEMOTION:
                        if all(
                            [
                                stone_x < self.board_size,
                                stone_y < self.board_size,
                                not (stone_x, stone_y) in Stone.stones,
                            ]
                        ):
                            Highlight(self, (stone_x, stone_y))
                        else:
                            StatButton.collide_event(e)
                    else:
                        self.claim((stone_x, stone_y))
                        self.evaluate_territories()
                        StatButton.click_detect(e)
            if running:
                if self.random:
                    self.randomise()
                self.render()
                clock.tick()
                print(clock.get_fps(), end="\r")


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    app = Application()
    app.run_game()
