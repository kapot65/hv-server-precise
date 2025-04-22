"""HV server logging module."""

import logging
import os

from config import LOG_FILE, LOG_LEVEL_CLI, LOG_LEVEL_FILE, PROJECT_ROOT


class RelativePathFormatter(logging.Formatter):
    def format(self, record):
        pathname = record.pathname
        if pathname.startswith(PROJECT_ROOT):
            record.pathname = os.path.relpath(pathname, PROJECT_ROOT)
        return super().format(record)


def init_logger(logger_name: str) -> None:
    """Initialize HV server logger."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(LOG_LEVEL_CLI)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(LOG_LEVEL_FILE)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(LOG_LEVEL_CLI)

    formatter = RelativePathFormatter("%(asctime)s %(levelname)s %(pathname)s:%(lineno)d - %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
