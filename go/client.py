# -*- coding: utf-8 -*-

import asyncio

from . import __version__
from .errors import DataException, ServerFullException, VersionException
from .models import Color, Position, Stone
from .networking import ClientServerBase, ConnectionBase
from .server import Mode
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
        self._connection = None

    async def _handshake(self):
        response = await self._connection.send_recv(f"go {__version__}")
        if response == "no":
            raise VersionException(f"Server does not support version {__version__}")
        elif response != f"ok {__version__}":
            raise DataException(f"Invalid handshake response {response!r}")

    async def _setup(self):
        status = await self._connection.recv()
        if status == "full":
            raise ServerFullException()
        elif not status.startswith("mode"):
            raise DataException(f"Invalid server status {status!r}")

        mode = status.split()[1].upper()
        if mode not in Mode.__members__:
            raise DataException(f"Server gave invalid server mode {mode!r}")

        mode = Mode[mode]
        if mode == Mode.NORMAL:
            try:
                color = await self._connection.recv()
                color = int(color)
            except ValueError:
                raise DataException(f"Color value {color!r} is not a valid integer")

            if color not in Color.__members__:
                raise DataException(f"{color} is not a valid Color value")
            self.color = Color(color)

        response = await self._connection.recv()
        if not response.startswith("stones"):
            raise DataException(f"Expected stones from server, got {response!r}")

        stones_string = response.split(maxsplit=1)[1]
        if len(stones_string) not in (81, 169, 361):
            raise DataException(
                f"Invalid number of stones represented, got {len(stones_string)}"
            )

        self.board_size = int(len(stones_string) ** 0.5)
        for y in range(self.board_size):
            for x in range(self.board_size):
                stone_char = stones_string[y * self.board_size + x]
                if stone_char.upper() == "X":
                    continue
                try:
                    color = int(stone_char)
                except ValueError:
                    raise DataException(f"{stone_char} is not a valid integer")

                if color not in Color.__members__:
                    raise DataException(f"{color} is not a valid Color value")

                color = Color(color)
                pos = Position(x, y)
                self.stones[pos] = Stone(pos, color)

        ready = await self._connection.send_recv("ack")
        if ready != "ready":
            raise DataException("Server did not respond ready")

    async def _connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self._connection = Connection(reader, writer)
        await self._handshake()
        await self._setup()

    async def disconnect(self):
        if self._connection is not None:
            await self._connection.close()

    async def _event_worker(self):
        while True:
            event = await self.ui._outgoing_event_q.get()
            if event.type == EventType.PLACE_STONE:
                self.game_state.place_stone(event.pos)
            self.ui._outgoing_event_q.task_done()

    async def run(self):
        await self._connect()
        self.ui = UI(self)

        asyncio.create_task(self._event_worker())
        await self.ui.run()

        await self._disconnect()
