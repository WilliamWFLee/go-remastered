# -*- coding: utf-8 -*-

import asyncio

from . import __version__
from .errors import DataException, ServerFullException, VersionException
from .models import Mode, Color, ClientState
from .networking import ClientServerBase, ConnectionBase
from .ui import UI, EventType

DEFAULT_HOST = "127.0.0.1"


class Connection(ConnectionBase):
    """
    Represents the client connection. Network communications happen via this class
    """

    pass


class Client(ClientServerBase):
    """
    Represents a client
    """

    def __init__(self, host=None, port=None, timeout=None):
        """
        Instantiates the client instance. This is usually done by the launcher
        """
        super().__init__(host=host if host else DEFAULT_HOST, port=port)
        self.state = ClientState()
        self.timeout = timeout
        self._connection = None

    async def _handshake(self):
        await self._connection.send("go", __version__)
        response = await self._connection.recv("no", "ok")
        if "ok" not in response:
            raise VersionException(f"Server does not support version {__version__}")
        elif response["ok"] != __version__:
            raise DataException(f"Invalid handshake response {response!r}")

    async def _setup(self):
        response = await self._connection.recv("full", "mode")
        if "full" in response:
            raise ServerFullException()

        self.state.mode = response["mode"]
        self.state.stones, self.state.board_size = (
            await self._connection.recv("stones")
        )["stones"]

        await self._connection.send("ack")
        await self._connection.recv("ready")

    async def _connect(self):
        reader, writer = await asyncio.open_connection(self.host, self.port)
        self._connection = Connection(reader, writer)
        await self._handshake()
        await self._setup()

    async def disconnect(self):
        """
        Disconnects the client from the server
        """
        if self._connection is not None:
            await self._connection.close()

    async def _event_worker(self):
        # Event worker for fetching game events from the UI event queue
        # and dispatching them to the server
        while True:
            event = await self.state._outgoing_event_q.get()
            # if event.type == EventType.PLACE_STONE:
            #     self.state.place_stone(event.pos)
            self.state._outgoing_event_q.task_done()

    async def run(self):
        """
        Runs the client and connects to the server
        """
        await self._connect()

        if self.state.mode == Mode.LOCAL:
            self.state.color = Color.BLACK
        self.ui = UI(self.state)

        await asyncio.gather(self._event_worker(), self.ui.run())
        await self._disconnect()
