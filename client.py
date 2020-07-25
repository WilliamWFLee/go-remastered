# -*- coding: utf-8 -*-

import asyncio

from config import ConfigDialog
from models import GameState
from ui import UI, EventType


class Client:
    def __init__(self):
        config_dialog = ConfigDialog()
        self.config = config_dialog.get_config()
        self.game_state = GameState(self.config.board_size)
        self.ui = UI(self.game_state, self.config.square_width)

    async def _event_worker(self):
        while True:
            event = await self.ui._outgoing_event_q.get()
            if event.type == EventType.PLACE_STONE:
                self.game_state.place_stone(event.pos)
            self.ui._outgoing_event_q.task_done()

    async def run(self):
        if self.config is not None:
            asyncio.create_task(self._event_worker())
            await self.ui.run()
