import asyncio
from asyncio import StreamReader, StreamWriter
from functools import partial
import json
from logging import Logger

import dfparser
from aiohttp import web, WSMsgType

# from hardware_manager_virtual import HVManagerVirtual as HVManager
from hardware_manager import HVManager
from manager import HardwareManager
from utils.cli import parse_args
from utils.logger import init_logger

async def socket_handler(reader: StreamReader, writer: StreamWriter, mgr: HardwareManager, log: Logger):
    peername = writer.get_extra_info('peername')
    log.debug(f'Connection from {peername}')

    subcription = asyncio.Queue()

    async def process_output():
        while True:
            # this can also await asyncio.sleep() or whatever is needed
            message = await subcription.get()
            meta = message['meta']
            data = message['data']

            if meta['answer_type'] == 'get_voltage':
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

    log.debug(f'Connection from {peername} closed')
    output_coro.cancel()
    mgr.output.subscriptions.remove(subcription)


async def websocket_handler(request, mgr: HardwareManager, log: Logger):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    subcription = asyncio.Queue()
    async def process_output():
        while True:
            message = await subcription.get()
            meta = message['meta']

            if meta['answer_type'] == 'get_voltage':
                await ws.send_str(json.dumps(meta))
            else:
                log.error('unhandled answer type %s', meta['answer_type'])

    mgr.output.subscriptions.add(subcription)
    output_coro = asyncio.create_task(process_output())

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            meta = json.loads(msg.data)
            logger.debug('ws > %s', meta)
            await mgr.input.put(dict(meta=meta, data=b''))
        elif msg.type == WSMsgType.BINARY:
            raise NotImplementedError('binary type is not supported')
        elif msg.type == WSMsgType.ERROR:
            logger.error('ws connection closed with exception %s', ws.exception())

    logger.info('websocket connection closed')
    output_coro.cancel()
    mgr.output.subscriptions.remove(subcription)

    return ws

async def index(request):
    return web.FileResponse('./static/index.html')


async def init_web(mgr: HardwareManager, log: Logger):
    """Aiohttp app.run alternative."""
    # TODO: Add more verbosity
    app = web.Application()
    app.add_routes([
        web.get('/', index),
        web.static('/assets', "./static/assets"),
        web.get('/channel', partial(websocket_handler, mgr=mgr, log=log)),
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner)
    await site.start()


if __name__ == "__main__":

    args = parse_args()
    logger = init_logger(args)
    manager = HVManager(logger)

    loop = asyncio.new_event_loop()

    routine_coro = loop.run_until_complete(manager.start())
    websockets_coro = loop.create_task(init_web(manager, logger))
    sockets_coro = asyncio.start_server(partial(socket_handler, mgr=manager, log=logger), '0.0.0.0', 5555)
    server = loop.run_until_complete(sockets_coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Programm stoped by user input")


    loop.run_until_complete(manager.stop())
    websockets_coro.cancel()
    server.close()
    loop.run_until_complete(server.wait_closed())
