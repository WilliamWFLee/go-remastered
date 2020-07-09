# -*- coding: utf-8 -*-
"""
A graphical version of the board game Go
Copyright (c) 2020 William Lee
"""

from config import ConfigDialog
from game import Go

def main():
    config_dialog = ConfigDialog()
    config = config_dialog.get_config()

    game = Go(**config._asdict())
    game.run()


main()
