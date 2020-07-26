# -*- coding: utf-8 -*-

import asyncio

from go.server import Server


async def main():
    server = Server()
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
