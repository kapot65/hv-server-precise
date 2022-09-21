"""Скрипт запуска сервера стойки HV."""
import asyncio
from asyncio.log import logger
from functools import partial
from logging import getLogger

from config import LOGGER_NAME

from utils.logger import init_logger
from utils.transport.socket import socket_handler
from utils.transport.websocket import init_web
from hv_manager import HVManager

if __name__ == "__main__":

    init_logger()
    logger = getLogger(LOGGER_NAME)
    manager = HVManager()

    loop = asyncio.new_event_loop()

    loop.run_until_complete(manager.start())

    server = loop.run_until_complete(
        asyncio.start_server(
            partial(socket_handler, mgr=manager),
            '0.0.0.0', 5555)
        )
    ws_server = loop.run_until_complete(init_web(manager))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Programm stoped by user input")

    loop.run_until_complete(manager.stop())
    server.close()
    loop.run_until_complete(server.wait_closed())
    if ws_server:
        loop.run_until_complete(ws_server.stop())
