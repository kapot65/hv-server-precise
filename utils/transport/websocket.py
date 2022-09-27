"""Websocket protocol handling."""
import asyncio
from functools import partial
import json

from logging import getLogger
from aiohttp import web

from config import LOGGER_NAME, WEB_INTERFACE_HOST, WEB_INTERFACE_PORT
from utils.manager import HardwareManager

_logger = getLogger(LOGGER_NAME)

async def __websocket_handler(request, mgr: HardwareManager):

    ws_res = web.WebSocketResponse()
    await ws_res.prepare(request)

    subcription = asyncio.Queue()
    async def process_output():
        while True:
            try:
                message = await subcription.get()
                meta = message['meta']
                print(json.dumps(meta))
                await ws_res.send_str(json.dumps(meta))
            except asyncio.CancelledError as exc:
                raise exc
            except RuntimeError as exc:
                if exc.args[0] == "Event loop is closed":
                    return
                else:
                    _logger.exception(exc)
            # pylint: disable-next=broad-except
            except Exception as exc:
                _logger.exception(exc)

    mgr.output.subscriptions.add(subcription)
    output_coro = asyncio.create_task(process_output())

    async for msg in ws_res:
        if msg.type == web.WSMsgType.TEXT:
            meta = json.loads(msg.data)
            _logger.debug('ws > %s', meta)
            await mgr.input.put(dict(meta=meta, data=b''))
        elif msg.type == web.WSMsgType.BINARY:
            raise NotImplementedError('binary type is not supported')
        elif msg.type == web.WSMsgType.ERROR:
            _logger.error('ws connection closed with exception %s', ws_res.exception())

    _logger.info('websocket connection closed')
    output_coro.cancel()
    mgr.output.subscriptions.remove(subcription)

    return ws_res

async def __index(_):
    return web.FileResponse('./utils/transport/static/index.html')


async def init_web(mgr: HardwareManager):
    """Aiohttp app.run alternative."""
    log = getLogger(LOGGER_NAME)
    try:
        # TODO: Add more verbosity
        app = web.Application()
        app.add_routes([
            web.get('/', __index),
            web.static('/assets', "./utils/transport/static/assets"),
            web.get('/channel', partial(__websocket_handler, mgr=mgr)),
        ])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            shutdown_timeout=1,
            host=WEB_INTERFACE_HOST,
            port=WEB_INTERFACE_PORT
        )
        await site.start()
        _logger.info(
            "Start web interface on %s:%i", 
            WEB_INTERFACE_HOST, WEB_INTERFACE_PORT)

        return site
    except asyncio.CancelledError as exc:
        raise exc
    # pylint: disable-next=broad-except
    except Exception as exc:
        log.exception(exc)
