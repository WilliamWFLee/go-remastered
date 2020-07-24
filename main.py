# -*- coding: utf-8 -*-
"""
A graphical version of the board game Go
Copyright (c) 2020 William Lee
"""

from config import ConfigDialog
from models import GameState
from ui import UI


def main():
    config_dialog = ConfigDialog()
    config = config_dialog.get_config()

    if config is not None:
        game_state = GameState(config.board_size)
        ui = UI(game_state, config.square_width)
        ui.run()


main()
