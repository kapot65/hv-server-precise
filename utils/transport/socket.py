"""Коннектор DataForge TCP/IP потока к :class:`utils.manager.HardwareManager`."""
import asyncio
from logging import getLogger

import dfparser

from config import LOGGER_NAME
from utils.manager import HardwareManager

async def socket_handler(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        mgr: HardwareManager):
    """Обработчик соединения TCP для :class:`utils.manager.HardwareManager`

    Функция предназначена для использования с :func:`asyncio.start_server`
    через :func:`functools.partial`. Пример:

    `start_server(partial(socket_handler, mgr=manager),...)`

    Функция транслирует без изменений сообщения в обе стороны
    (TCP/IP -> HardwareManager.input, HardwareManager.output -> TCP/IP)
    Для сериализации/парсинга используется формат DataForge Envelope.

    Args:
        reader (asyncio.StreamReader): стандартный аргумент для `asyncio.start_server`
        writer (asyncio.StreamWriter): стандартный аргумент для `asyncio.start_server`
        mgr (HardwareManager): класс для управления оборудованием
    """
    log = getLogger(LOGGER_NAME)

    peername = writer.get_extra_info('peername')
    log.debug('Connection from %s', peername)

    subcription = asyncio.Queue()

    async def process_output():
        while True:
            message = await subcription.get()
            meta = message['meta']
            data = message['data']

            writer.write(dfparser.create_message(meta, data))
            await writer.drain()

    mgr.output.subscriptions.add(subcription)
    output_coro = asyncio.create_task(process_output())

    buffer = b''

    while not writer.is_closing() and not reader.at_eof():
        buffer += await reader.read(1024)
        messages, buffer = dfparser.get_messages_from_stream(buffer)
        for message in messages:
            await mgr.input.put(message)

    log.debug('Connection from %s closed', peername)
    output_coro.cancel()
    mgr.output.subscriptions.remove(subcription)
