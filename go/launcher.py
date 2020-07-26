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

Config = namedtuple("Config", "board_size square_width")


class Launcher:
    """
    Dialog for getting game config from user
    """

    def __init__(self):
        self._root = Tk()
        self._root.title("Go Launcher")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Board size input box
        self._size_label = Label(self._root, text="Board Size (9, 13, or [19])")
        self._size_label.grid(row=0, column=0, sticky=W, **PADDING)
        self._size_entry = Entry(self._root)
        self._size_entry.grid(row=0, column=1, **PADDING)

        # Square width input box
        self._square_width_label = Label(self._root, text="Square Width [50]")
        self._square_width_label.grid(row=1, column=0, sticky=W, **PADDING)
        self._square_width_entry = Entry(self._root)
        self._square_width_entry.grid(row=1, column=1, **PADDING)

        # Go button
        self._go_button = Button(
            self._root, text="Go!", command=self.set_config, padx=40
        )
        self._go_button.grid(row=2, column=0, columnspan=2, **PADDING)
        self._root.bind("<Return>", lambda e: self.set_config())

    def on_close(self) -> None:
        self.config = None
        self._root.destroy()

    def set_config(self) -> None:
        self._size_label.config(fg="#000")
        self._square_width_label.config(fg="#000")

        board_size = self._size_entry.get()
        square_width = self._square_width_entry.get()

        board_size = int(board_size) if board_size else 0
        square_width = int(square_width) if square_width else 0

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

        if not square_width:
            square_width = None
        elif square_width < 5:
            messagebox.showerror(
                title="Error",
                message=(
                    f"Chosen square width ({square_width}) is too small."
                    "Game will not render correctly"
                ),
            )
            self._square_width_label.config(fg="red")
            return
        elif square_width < 15:
            messagebox.showwarning(
                title="Warning",
                message=(
                    f"Chosen square width ({square_width}) " "may make text unreadable"
                ),
            )
        elif square_width < 10:
            messagebox.showwarning(
                title="Warning",
                message=(
                    f"Chosen square width ({square_width}) "
                    "may make game challenging to play"
                ),
            )

        self.config = Config(board_size=board_size, square_width=square_width)

        # Destroys Tk root if config is successful
        self._root.destroy()

    def get_config(self) -> Config:
        self._root.mainloop()
        return self.config
