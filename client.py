# -*- coding: utf-8 -*-

import asyncio
from typing import Optional

from config import ConfigDialog
from models import GameState
from networking import ClientServerBase, ConnectionBase
from ui import UI, EventType


DEFAULT_HOST = "127.0.0.1"


class ResponseException(Exception):
    pass


class Connection(ConnectionBase):
    pass


class Client(ClientServerBase):
    def __init__(
        self, host=None, port=None, timeout: Optional[float] = None,
    ):
        super().__init__(host=host if host else DEFAULT_HOST, port=port)

        config_dialog = ConfigDialog()
        self.config = config_dialog.get_config()
        self.game_state = GameState(self.config.board_size)
        self.ui = UI(self.game_state, self.config.square_width)

        self.timeout = timeout

    async def _connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self._connection = Connection(reader, writer)
        await self._handshake()

    async def _handshake(self):
        await self._connection.send("go")

        response = await self._connection.recv()
        if response != "ok":
            raise ResponseException(f"Invalid handshake response {response!r}")

    async def _event_worker(self):
        while True:
            event = await self.ui._outgoing_event_q.get()
            if event.type == EventType.PLACE_STONE:
                self.game_state.place_stone(event.pos)
            self.ui._outgoing_event_q.task_done()

    async def run(self):
        if self.config is not None:
            await self._connect()

            asyncio.create_task(self._event_worker())
            await self.ui.run()

            self._connection.writer.close()
            await self._connection.writer.wait_closed()
