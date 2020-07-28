Client-server protocol
======================

This document details the protocol used for communicate between a Go client and a Go server.

All messages are terminated by ``\n``, so for example the message ``hello`` would be sent as ``hello\n``

Handshake
---------

First, a handshake is performed to establish the connection and setup.

1. The client sends ``go <version>``, where ``<version>`` is ``__version__`` found in ``__init__.py``, to the server to initiate the connection.
2. The server must then respond with\:

   a. ``ok <version>``, where ``<version>`` matches the one sent by the client, if the client version is compatible with the server; or
   b. ``no`` if versions are not compatible, and the handshake fails.

3. If the server fails to respond, the handshake fails.

Setup
-----

Game setup then happens to establish compatibility and initial state of the game.

1. The server sends ``full`` if the server all client slots are occupied. There are two slots, one for each player, on a regular server, or a single slot for a local game.

   a. The connection ends if ``full`` is sent.

2. The server sends ``mode <mode>`` where ``<mode>`` is either ``local`` if the server runs a local game or ``normal`` if the server runs a regular server.

   a. If ``<mode>`` is ``LOCAL``, then it is implied that the client connecting is the sole client.
   b. If ``<mode>`` is ``NORMAL``, then the server sends ``color <color>``, ``<color>`` is whatever color the client is assigned: 0 for black, 1 for white

3. The server sends ``stones <stones>`` where ``<stones>`` is a string detailing the state of each intersection on the board, from left to right, top to bottom, starting from the top-left. For each intersection, the string contains an ``X`` for an empty intersection, ``0`` for a black stone and ``1`` for a white stone. For example if we have a hypothetical 2x2 board with a black stone in the top-left corner, a white stone in the top-right corner, and empty intersections elsewhere, then ``<stones>`` would be ``01XX``.

   a. The length of the string must be of length 81, 169 or 361 for board sizes 9, 13 or 19 respectively.

4. The client responds with ``ack`` to acknowledge.

5. Finally, the server sends ``ready`` to indicate it is ready for subsequent communication.

Main
----

Over the course of the game, there are three events that can occur: a turn is taken, and therefore another client is allowed to place a stone; a stone is placed on the board in a turn; and a stone or stones is/are removed from the board.

Indicating turn
---------------

1. The server sends ``yourturn`` to the client whose turn it is.
2. The client responds ``ack`` to acknowledge.

Stone placement
---------------

1. The client sends ``place <x> <y>`` where ``<x>`` and ``<y>`` are the coordinates of the stone to be placed, so ``place 0 0`` would be the top-left intersection on the board, and ``place 18 18`` would be the bottom-right intersection for a 19x19 board.
2. The server then broadcasts ``place <color> <x> <y>`` to all clients, including the sender, where ``<color>`` is ``0`` for black or ``1`` for white.

   a. Each client sends back ``ack`` to acknowledge the placement.

3. The server then sends ``ack`` back to the sender.


Stone removal
-------------

A removal of a stone only happens when a placement of a stone causes stones to be captured according to the rules of the game.

1. The server sends ``remove <x1> <y1> <x2> <y2> ... <xn> <yn>``, where each pair ``<xi> <yi>`` is a pair of coordinates for the stone to be removed.
2. The client sends ``ack`` to the server to acknowledge the removal(s).

Ending connection
-----------------

Both client and server are able to indicate if they are ending the connection by sending ``close`` and then ending the connection immediately after.
