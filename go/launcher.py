# -*- coding: utf-8 -*-
"""
Initiates launcher, and gets game config from user
"""

from collections import namedtuple
from tkinter import Button, Entry, Label, Tk, W, messagebox

PADDING = {
    "padx": 10,
    "pady": 5,
}

Config = namedtuple("Config", "board_size")


class Launcher:
    """
    Dialog for getting game config from user
    """

    def __init__(self):
        self._root = Tk()
        self._root.title("Go Launcher")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._local_game_button = Button(
            self._root,
            text="Play locally",
            command=self._show_local_game_setup,
            padx=40,
        )

        # Board size input box
        self._size_label = Label(self._root, text="Board Size (9, 13, or [19])")
        self._size_entry = Entry(self._root)

        # Go button
        self._go_button = Button(
            self._root, text="Go!", command=self.set_config, padx=40
        )

        self._widgets = [
            self._local_game_button,
            self._size_label,
            self._size_entry,
            self._go_button,
        ]

        self._show_main_menu()

    def _screen_change(self):
        for widget in self._widgets:
            widget.grid_forget()

    def _show_main_menu(self):
        self._local_game_button.grid(row=0, column=0, **PADDING)

    def _show_local_game_setup(self):
        self._screen_change()

        self._size_label.grid(row=0, column=0, sticky=W, **PADDING)
        self._size_entry.grid(row=0, column=1, **PADDING)

        self._go_button.grid(row=2, column=0, columnspan=2, **PADDING)
        self._root.bind("<Return>", lambda e: self.set_config())

    def _on_close(self) -> None:
        self.config = None
        self._root.destroy()

    def set_config(self) -> None:
        self._size_label.config(fg="#000")

        board_size = self._size_entry.get()
        board_size = int(board_size) if board_size else 0

        if not board_size:
            board_size = None
        elif board_size not in (9, 13, 19):
            messagebox.showerror(
                title="Error",
                message=f"{board_size} is not a valid board size\n"
                "Valid board sizes are 9, 13 and 19",
            )
            self._size_label.config(fg="red")
            return

        self.config = Config(board_size=board_size)

        # Destroys Tk root if config is successful
        self._root.destroy()

    def get_config(self) -> Config:
        self._root.mainloop()
        return self.config
