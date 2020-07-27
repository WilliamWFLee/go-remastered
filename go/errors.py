# -*- coding: utf-8 -*-

"""
Module for exceptions raised in the game
"""


class ConnectionException(Exception):
    """
    Base class of all connection-related exceptions
    """

    pass


class ConnectionCloseException(ConnectionException):
    """
    The connection has closed unexpectedly
    """

    pass


class ConnectionTimeoutError(ConnectionException):
    """
    A connection operation has timed out
    """

    pass


class HandshakeException(ConnectionException):
    """
    Initial connection handshake has failed
    """

    pass


class VersionException(HandshakeException):
    """
    Handshake has failed because of version incompatibilities
    """

    pass


class ServerFullException(ConnectionException):
    """
    The server cannot accept any more clients
    """

    pass


class DataException(ConnectionException):
    """
    The data received is not of the correct format
    """

    pass
