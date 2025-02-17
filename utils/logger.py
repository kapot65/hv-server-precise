"""HV server logging module."""

import logging

from config import LOG_FILE, LOG_LEVEL


def init_logger(logger_name: str) -> None:
    """Initialize HV server logger."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(LOG_LEVEL)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(LOG_LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL)

    fmt = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
