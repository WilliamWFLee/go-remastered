# -*- coding: utf-8 -*-
"""
A graphical version of the board game Go
Copyright (c) 2020 William Lee
"""

import asyncio

from client import Client


async def main():
    client = Client()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())
