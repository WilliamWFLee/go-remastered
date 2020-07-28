# -*- coding: utf-8 -*-

import asyncio
from typing import Any

from .errors import ConnectionTimeoutError, DataException
from .models import Mode, Position, Stone, Color

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

    def _serialize(self, key: str = "", value: Any = None):
        serialized = ""
        if key in ("go", "ok"):
            serialized = f"{value}"
        elif key == "mode":
            serialized = f"{value.name.upper()}"
        elif key == "stones":
            stones, board_size = value
            serialized = ""
            for y in range(board_size):
                for x in range(board_size):
                    pos = Position(x, y)
                    if pos not in stones:
                        serialized += "X"
                    else:
                        stone = stones[pos]
                        serialized += self._serialize(value=stone.color)
        elif key == "color":
            serialized = f"{value.value}"

        return f"{f'{key} ' if key else ''}{serialized}\n"

    def _deserialize(self, data: str):
        key, *value = data.split(maxsplit=1)
        if not value:
            return (key, None)
        value = value[0]
        if key in ("ok", "go"):
            return (key, value)
        if key == "mode":
            if value not in Mode.__members__:
                raise DataException(f"{value!r} is not a valid mode")
            return (key, Mode[value])

        if key == "stones":
            if len(value) not in (81, 169, 361):
                raise DataException(
                    f"Invalid number of stones represented, got {len(value)}"
                )

            board_size = int(len(value) ** 0.5)
            stones = {}
            for y in range(board_size):
                for x in range(board_size):
                    stone_char = value[y * board_size + x]
                    if stone_char.upper() == "X":
                        continue
                    color = self._deserialize(f"color {stone_char}")
                    pos = Position(x, y)
                    stones[pos] = Stone(pos, color)

            return (key, (stones, board_size))
        if key == "color":
            try:
                color_value = int(value)
            except ValueError:
                raise DataException(
                    f"{value!r} is not a valid representation of a integer"
                )

            try:
                return (key, Color(color_value))
            except ValueError:
                raise DataException(f"{color_value} is not a valid color value")

    async def send(self, key, value=None):
        data = self._serialize(key, value)
        self.writer.write(data.encode())
        await self.writer.drain()

    async def recv(self, *keys):
        try:
            data = await asyncio.wait_for(
                self.reader.readuntil(b"\n"), timeout=self.timeout
            )
            key, value = self._deserialize(data[:-1].decode())
            if key not in keys:
                raise DataException(f"Expected key to be one of {keys}, got {key!r}")
            return value
        except asyncio.TimeoutError:
            raise ConnectionTimeoutError("Timeout exceeded.")

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
