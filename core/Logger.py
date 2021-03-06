"""Logger.py

A Generic logging class.
"""

import logging

from core.core import log_fn


class Logger:
    """A flexible logger."""

    def __init__(
        self,
        module_name,
        file_name=log_fn,
        file_mode="w",
        file_handler_level=logging.DEBUG,
        file_handler_format="%(asctime)-15s [%(threadName)-12s][%(levelname)-8s]  %(message)s",
        console_handler=logging.StreamHandler(),
        console_handler_level=logging.DEBUG,
        console_handler_format=logging.Formatter(
            "%(asctime)-15s [%(threadName)-12s][%(levelname)-8s]  %(message)s"
        ),
    ):
        """Initialize the logger."""
        logging.basicConfig(
            level=file_handler_level,
            format=file_handler_format,
            filename=file_name,
            filemode=file_mode,
        )

        self.log = logging.getLogger(module_name)
        console_handler.setLevel(console_handler_level)
        console_handler.setFormatter(console_handler_format)
        self.log.addHandler(console_handler)
