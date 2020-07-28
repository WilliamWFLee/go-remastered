# -*- coding: utf-8 -*-

import asyncio

from . import __version__
from .errors import DataException
from .models import GameState
from .networking import ClientServerBase, ConnectionBase

DEFAULT_HOST = "0.0.0.0"


class Connection(ConnectionBase):
    """
    Represents the server's connection to a client
    """
    def __init__(self, server, reader, writer, timeout=None):
        super().__init__(reader, writer, timeout=timeout)
        self.server = server

    async def _handshake(self):
        try:
            version = await self.recv("go")
        except DataException:
            raise DataException("Invalid handshake request")

        if version != __version__:
            await self.send("no")
        else:
            await self.send("ok", version)

    async def _setup(self):
        await self.send("mode", self.server.mode)
        await self.send(
            "stones", (self.server.game_state.stones, self.server.game_state.board_size)
        )
        await self.recv("ack")
        await self.send("ready")

    async def serve(self):
        """
        Serves the connection to the client
        """
        await self._handshake()
        await self._setup()


class Server(ClientServerBase):
    """
    Represents the server
    """
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
        """
        Opens the server for listening
        """
        self.server = await asyncio.start_server(self._connected, self.host, self.port)
        async with self.server:
            await self.server.serve_forever()

    async def close(self):
        """
        Closes the server and its connections
        """
        for connection in self._connections:
            await connection.close()

        self.server.close()
        await self.server.wait_closed()


if __name__ == "__main__":
    asyncio.run(Server().serve())
