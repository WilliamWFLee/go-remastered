# -*- coding: utf-8 -*-

import logging
import sys

__version__ = "0.1.0"


# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter(
    "[{asctime}][{levelname}] {name}: {message}", "%Y-%m-%d %H:%M:%S", "{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Clean up namespace
del logger, handler, formatter
