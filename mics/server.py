#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 15:21:37 2017

@author: chernov
"""

import asyncio
from random import randint, random

from aiohttp import web, WSMsgType
from dftcp import DataforgeEnvelopeProtocol

from utils.cli import parse_args
from utils.logger import init_logger

class Hub():
    def __init__(self):
        self.subscriptions = set()

    def publish(self, message):
        for queue in self.subscriptions:
            queue.put_nowait(message)

voltageHub = Hub()

async def voltage_routine():
    """AAAA"""
    while True:
        await asyncio.sleep(3. + (random() - 0.5) * 2.)
        voltage = 100 + randint(-20, 20)
        logger.info('new voltage: %s', voltage)
        voltageHub.publish(voltage)

class HVServer(DataforgeEnvelopeProtocol):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscription = asyncio.Queue()

    async def _monitor_impl(self):
        while True:
            # this can also await asyncio.sleep() or whatever is needed
            voltage = await self.subscription.get()
            self.send_message(dict(
                type='answer',
                answer_type='get_voltage',
                block=1,
                voltage=voltage
            ))

    def connection_made(self, transport):
        logger.info("connection_made")
        super().connection_made(transport)
        loop_impl = asyncio.get_event_loop()

        voltageHub.subscriptions.add(self.subscription)
        print(list(voltageHub.subscriptions))
        self.monitor = loop_impl.create_task(self._monitor_impl())
    
    def connection_lost(self, exc):
        logger.info("connection_lost")
        voltageHub.subscriptions.remove(self.subscription)
        self.monitor.cancel()

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

app = web.Application()
app.add_routes([web.get('/channel', websocket_handler),])

async def init_web():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner)
    await site.start()


if __name__ == "__main__":
    args = parse_args()
    
    # if not "logger" in globals():
    logger = init_logger(args)

    loop = asyncio.new_event_loop() # TODO: compare to get_event_loop
    voltageCoro = loop.create_task(voltage_routine())

    webCoro = loop.create_task(init_web())

    coro = loop.create_server(HVServer, "0.0.0.0", args.work_port)
    server = loop.run_until_complete(coro)
 
    print(f'Serving on {server.sockets[0].getsockname()}')
    logger.info('Serving on %s', server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Programm stoped by user input")
        
    voltageCoro.cancel()
    webCoro.cancel()

    server.close()  
    loop.run_until_complete(server.wait_closed())
