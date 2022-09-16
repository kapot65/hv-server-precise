"""Модуль для работы с аппаратной частью стойки HV
"""
# TODO: переделать в класс

import asyncio

from utils.hub import Hub

INPUT = asyncio.Queue()

OUTPUT = Hub()

async def routine():
    """AAAA"""
    message_coro =  asyncio.create_task(__process_message__())
    monitor_coro = asyncio.create_task(__monitor_voltage__())


__curr_voltage__ = 0
__desired_voltage__ = 0
__CHANGE_SPEED_ = 100
async def __process_message__():
    while True:
        message = await INPUT.get()
        header = message['header']
        meta = message['meta']
        data = message['data']
        if(meta['command_type'] == 'set_voltage'):
            global __desired_voltage__
            __desired_voltage__ = float(meta['voltage'])
            print(f'setting {__desired_voltage__}')
        else:
            print(meta)


async def __monitor_voltage__():
    while True:
        global __curr_voltage__

        print(f'curr: {__curr_voltage__}, desired: {__desired_voltage__}')
        # dfparser.create_message.send_message()
        OUTPUT.publish(dict(meta=dict(
                type='answer',
                answer_type='get_voltage',
                block=1,
                voltage=__curr_voltage__
        ), data=b''))

        await asyncio.sleep(5)
        sign = 1 if __desired_voltage__ > __curr_voltage__ else -1
        delta = abs(__curr_voltage__ - __desired_voltage__)

        __curr_voltage__ += sign * min(__CHANGE_SPEED_ * 5, delta)
