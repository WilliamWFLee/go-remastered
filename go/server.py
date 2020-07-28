# -*- coding: utf-8 -*-

import asyncio
from enum import Enum, auto

from . import __version__
from .errors import DataException
from .models import GameState, Position
from .networking import ClientServerBase, ConnectionBase

DEFAULT_HOST = "0.0.0.0"


class Mode(Enum):
    LOCAL = auto()
    NORMAL = auto()


class Connection(ConnectionBase):
    def __init__(self, server, reader, writer, timeout=None):
        super().__init__(reader, writer, timeout=timeout)
        self.server = server

    async def _handshake(self):
        request = await self.recv()
        if not request.startswith("go"):
            raise DataException(f"Invalid handshake request {request!r}")
        elif request != f"go {__version__}":
            await self.send("no")
        else:
            await self.send(f"ok {request.split()[1]}")

    async def _setup(self):
        await self.send(f"mode {self.server.mode.name.lower()}")

        stones_string = ""
        for y in range(self.server.game_state.board_size):
            for x in range(self.server.game_state.board_size):
                pos = Position(x, y)
                if pos not in self.server.game_state.stones:
                    stones_string += "x"
                else:
                    stone = self.server.game_state.stones[pos]
                    stones_string += stone.color.value

        await self.send(f"stones {stones_string}")
        await self.send("ready")

    async def serve(self):
        await self._handshake()
        await self._setup()


class Server(ClientServerBase):
    def __init__(self, board_size, host=None, port=None, *, mode):
        super().__init__(host if host else DEFAULT_HOST, port=port)
        self.mode = mode
        self.game_state = GameState(board_size)
        self._connections = []

    async def _connected(self, reader, writer):
        connection = Connection(self, reader, writer)
        self._connections += [connection]
        await connection.serve()

    async def serve(self):
        self.server = await asyncio.start_server(self._connected, self.host, self.port)
        async with self.server:
            await self.server.serve_forever()

    async def close(self):
        for connection in self._connections:
            await connection.close()

        self.server.close()
        await self.server.wait_closed()


if __name__ == "__main__":
    asyncio.run(Server().serve())
