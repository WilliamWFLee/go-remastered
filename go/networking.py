# -*- coding: utf-8 -*-

import asyncio

DEFAULT_PORT = 18255


class ClientServerBase:
    def __init__(self, host, port=None):
        self.host = host
        self.port = port if port else DEFAULT_PORT


class ConnectionBase:
    def __init__(self, reader, writer, timeout=None):
        self.reader = reader
        self.writer = writer
        self.timeout = timeout

    async def send(self, data: str):
        self.writer.write(data.encode() + b"\n")
        await self.writer.drain()

    async def recv(self):
        try:
            data = await asyncio.wait_for(
                self.reader.readuntil(b"\n"), timeout=self.timeout
            )
            return data[:-1].decode()
        except asyncio.TimeoutError:
            pass

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
