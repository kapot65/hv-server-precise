"""Скрипт запуска сервера стойки HV."""
import asyncio
from functools import partial
from logging import getLogger

from config import LOGGER_NAME, TCP_INTERFACE_HOST, TCP_INTERFACE_PORT

from utils.logger import init_logger
from utils.transport.socket import socket_handler
from utils.transport.websocket import init_web
from hv_manager import HVManager

if __name__ == "__main__":

    init_logger()
    _logger = getLogger(LOGGER_NAME)
    manager = HVManager()

    loop = asyncio.new_event_loop()

    loop.run_until_complete(manager.start())

    server = loop.run_until_complete(
        asyncio.start_server(
            partial(socket_handler, mgr=manager),
            TCP_INTERFACE_HOST, TCP_INTERFACE_PORT)
        )
    _logger.info(
        "Start TCP/IP interface on %s:%i",
        TCP_INTERFACE_HOST, TCP_INTERFACE_PORT
    )
    ws_server = loop.run_until_complete(init_web(manager))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        _logger.info("Programm stoped by user input")

    loop.run_until_complete(manager.stop())
    server.close()
    loop.run_until_complete(server.wait_closed())
    if ws_server:
        loop.run_until_complete(ws_server.stop())
