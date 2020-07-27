# -*- coding: utf-8 -*-

import asyncio

from .networking import ClientServerBase, ConnectionBase


DEFAULT_HOST = "0.0.0.0"


class Connection(ConnectionBase):
    async def serve(self):
        await self.recv()
        await self.send("ok")


class Server(ClientServerBase):
    def __init__(self, host=None, port=None):
        super().__init__(host if host else DEFAULT_HOST, port=port)
        self._connections = []

    async def _connected(self, reader, writer):
        connection = Connection(reader, writer)
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
