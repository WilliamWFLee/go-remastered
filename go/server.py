# -*- coding: utf-8 -*-

import asyncio

from . import __version__
from .networking import ClientServerBase, ConnectionBase
from .errors import DataException

DEFAULT_HOST = "0.0.0.0"


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
            await self.send(f"ok {__version__}")

    async def serve(self):
        await self._handshake()


class Server(ClientServerBase):
    def __init__(self, host=None, port=None):
        super().__init__(host if host else DEFAULT_HOST, port=port)
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
