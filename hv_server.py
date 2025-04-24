"""Скрипт запуска сервера стойки HV."""

import asyncio
import os
from functools import partial
from logging import Logger, getLogger
from typing import Optional

from config import (
    DB_SYNC_COMMAND,
    DB_SYNC_INTERVAL,
    LOGGER_NAME,
    TCP_INTERFACE_HOST,
    TCP_INTERFACE_PORT,
)
from db import DailyTsvWriter
from hv_manager import HVManager
from utils.logger import init_logger
from utils.transport.socket import socket_handler
from utils.transport.websocket import init_web


async def sync_db_loop(cmd: str, interval: float, logger: Optional[Logger] = None):
    while True:
        if logger:
            logger.info(f"start database syncing ({cmd})")
        os.system(cmd)
        if logger:
            logger.info("database synced")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    init_logger(LOGGER_NAME)
    _logger = getLogger(LOGGER_NAME)

    __db_writer = DailyTsvWriter("HV")

    manager = HVManager(__db_writer)

    loop = asyncio.new_event_loop()

    __sync_db_loop = None
    if DB_SYNC_COMMAND:
        __sync_db_loop = loop.create_task(sync_db_loop(DB_SYNC_COMMAND, DB_SYNC_INTERVAL, _logger))

    loop.run_until_complete(manager.start())

    server = loop.run_until_complete(
        asyncio.start_server(
            partial(socket_handler, mgr=manager), TCP_INTERFACE_HOST, TCP_INTERFACE_PORT
        )
    )
    _logger.info(
        "Start TCP/IP interface on %s:%i", TCP_INTERFACE_HOST, TCP_INTERFACE_PORT
    )
    ws_server = loop.run_until_complete(init_web(manager))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        _logger.info("Programm stoped by user input")

    # Синхронизация базы данных перед завершением программы
    if DB_SYNC_COMMAND:
        __sync_db_loop.cancel()
        os.system(DB_SYNC_COMMAND)

    loop.run_until_complete(manager.stop())
    server.close()
    loop.run_until_complete(server.wait_closed())
    if ws_server:
        loop.run_until_complete(ws_server.stop())
    