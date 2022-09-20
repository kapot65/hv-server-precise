"""Модуль для работы с аппаратной частью стойки HV 
"""
# TODO: переделать в класс

import asyncio
from logging import Logger
from random import random

from manager import HardwareManager

class HVManagerVirtual(HardwareManager):

    __CHANGE_SPEED = 100

    def __init__(self, logger: Logger):
        super().__init__()
        self.__logger = logger
        self.__curr_voltage = 0
        self.__desired_voltage = 0

        self.__message_coro =  None
        self.__monitor_coro = None

    async def __process_message(self):
        while True:
            try:
                message = await self.input.get()
                self.__logger.debug(message)
                meta = message['meta']
                if(meta['command_type'] == 'set_voltage'):
                    self.__desired_voltage = float(meta['voltage'])
                    self.__logger.debug(f'setting {self.__desired_voltage}')
                else:
                    self.__logger.debug(meta)
            except asyncio.CancelledError as exc:
                raise exc
            except Exception as exc:
                self.__logger.exception(exc)


    async def __monitor_voltage(self):
        while True:
            try:
                self.__logger.debug(f'curr: {self.__curr_voltage}, desired: {self.__desired_voltage}')
                self.output.publish(dict(meta=dict(
                        type='answer',
                        answer_type='get_voltage',
                        block=1,
                        voltage=self.__curr_voltage
                ), data=b''))

                await asyncio.sleep(5)
                sign = 1 if self.__desired_voltage > self.__curr_voltage else -1
                delta = abs(self.__curr_voltage - self.__desired_voltage)

                self.__curr_voltage += sign * min(HVManagerVirtual.__CHANGE_SPEED * 5, delta) + (random() - 0.5) * 2.0
            except asyncio.CancelledError as exc:
                raise exc
            except Exception as exc:
                self.__logger.exception(exc)

    async def start(self):
        self.__message_coro =  asyncio.create_task(self.__process_message())
        self.__monitor_coro = asyncio.create_task(self.__monitor_voltage())

    async def stop(self):
        if self.__message_coro:
            self.__message_coro.cancel()
            self.__message_coro = None

        if self.__monitor_coro:
            self.__monitor_coro.cancel()
            self.__monitor_coro = None
