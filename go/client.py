# -*- coding: utf-8 -*-

import asyncio

from . import __version__
from .errors import DataException, VersionException
from .networking import ClientServerBase, ConnectionBase
from .ui import UI, EventType

DEFAULT_HOST = "127.0.0.1"


class Connection(ConnectionBase):
    pass


class Client(ClientServerBase):
    def __init__(self, host=None, port=None, timeout=None):
        super().__init__(host=host if host else DEFAULT_HOST, port=port)
        self.board_size = None
        self.stones = {}
        self.color = None
        self.timeout = timeout

    async def _connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self._connection = Connection(reader, writer)
        await self._handshake()

    async def _disconnect(self):
        await self._connection.close()

    async def _handshake(self):
        response = await self._connection.send_recv(f"go {__version__}")
        if response == "no":
            raise VersionException(f"Server does not support version {__version__}")
        elif response != f"ok {__version__}":
            raise DataException(f"Invalid handshake response {response!r}")

    async def _event_worker(self):
        while True:
            event = await self.ui._outgoing_event_q.get()
            if event.type == EventType.PLACE_STONE:
                self.game_state.place_stone(event.pos)
            self.ui._outgoing_event_q.task_done()

    async def run(self):
        await self._connect()

        asyncio.create_task(self._event_worker())
        self.ui = UI(self)
        await self.ui.run()

        await self._disconnect()
