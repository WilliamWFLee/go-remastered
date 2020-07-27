# -*- coding: utf-8 -*-
"""
Initiates launcher, and gets game config from user
"""

import asyncio
from collections import namedtuple
from tkinter import Button, Entry, Label, Tk, W, messagebox

from .client import Client
from .server import Server

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

        # Button to hold local game
        self._local_game_button = Button(
            self._root,
            text="Play locally",
            command=self._show_local_game_setup,
            padx=40,
        )

        # Button to host a game
        self._host_game_button = Button(
            self._root, text="Host a game", command=self._show_host_game_setup, padx=40
        )

        # Host input box
        self._host_label = Label(self._root, text="Address [0.0.0.0]")
        self._host_entry = Entry(self._root)

        # Port input box
        self._port_label = Label(self._root, text="Port [18255]")
        self._port_entry = Entry(self._root)

        # Board size input box
        self._size_label = Label(self._root, text="Board Size (9, 13, or [19])")
        self._size_entry = Entry(self._root)

        # Stores command to execute for launch
        self._go_command = lambda: None

        # Go button
        self._go_button = Button(
            self._root, text="Go!", command=lambda: self._go_command(), padx=40
        )
        self._root.bind("<Return>", self._go_command)

        self._widgets = [
            self._local_game_button,
            self._host_game_button,
            self._host_label,
            self._host_entry,
            self._port_label,
            self._port_entry,
            self._size_label,
            self._size_entry,
            self._go_button,
        ]

        self._show_main_menu()

    def _screen_change(self):
        for widget in self._widgets:
            widget.grid_forget()

        self._go_command = lambda: None

    def _show_main_menu(self):
        self._screen_change()

        self._local_game_button.grid(row=0, **PADDING)
        self._host_game_button.grid(row=1, **PADDING)

    def _show_local_game_setup(self):
        self._screen_change()
        self._go_command = lambda: asyncio.run(self.launch_local_game())

        self._size_label.grid(row=0, column=0, sticky=W, **PADDING)
        self._size_entry.grid(row=0, column=1, **PADDING)

        self._go_button.grid(row=1, column=0, columnspan=2, **PADDING)

    def _show_host_game_setup(self):
        self._screen_change()

        self._host_label.grid(row=0, column=0, sticky=W, **PADDING)
        self._host_entry.grid(row=0, column=1, **PADDING)

        self._port_label(row=1, column=0, sticky=W, **PADDING)
        self._port_entry.grid(row=1, column=1, **PADDING)

        self._go_button.grid(row=2, column=0, columnspan=2, **PADDING)

    def _on_close(self):
        self.config = None
        self._root.destroy()

    async def run_server(self, host=None, port=None):
        self.server = Server(host=host, port=port)
        await self.server.serve()

    async def launch_local_game(self):
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

        # Destroys Tk root if config is successful
        self._root.withdraw()

        asyncio.create_task(self.run_server("127.0.0.1"))

        self.client = Client(board_size=board_size)
        await self.client.run()

        await self.server.close()
        self._root.destroy()

    def mainloop(self) -> None:
        self._root.mainloop()
