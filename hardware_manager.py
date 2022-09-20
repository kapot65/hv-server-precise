"""Модуль для работы с аппаратной частью стойки HV 
"""
# TODO: переделать в класс

import asyncio
import sys
from logging import Logger
from random import random

import pyvisa as visa

from manager import HardwareManager

class HVManager(HardwareManager):

    def __init__(self, logger: Logger):
        super().__init__()
        self.__logger = logger
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
                VISA_ADDRESS = 'GPIB::20::INSTR'

                try:
                    # Create a connection (session) to the instrument
                    resourceManager = visa.ResourceManager()
                    session = resourceManager.open_resource(VISA_ADDRESS)
                except visa.Error as ex:
                    self.__logger.error('Couldn\'t connect to \'%s\', exiting now...', VISA_ADDRESS)
                    sys.exit() # TODO: change to adequate exit


                self.__logger.debug("*RST")
                session.write("*RST")
                await asyncio.sleep(1.0)
                self.__logger.debug("CONF:VOLT:DC 10,0.00001")
                session.write("CONF:VOLT:DC 10,0.00001")
                await asyncio.sleep(1)
                self.__logger.debug("DET:BAND 3")
                session.write("DET:BAND 3")
                await asyncio.sleep(1)
                # self.__logger.debug("INP:IMP:AUTO ON")
                # session.write("INP:IMP:AUTO ON")
                # await asyncio.sleep(1)
                self.__logger.debug("VOLT:NPLC 100")
                session.write("VOLT:NPLC 100")
                await asyncio.sleep(1)

                self.__logger.debug('voltmeter initialization done')

                while True:

                    session.write('READ?')
                    await asyncio.sleep(4)
                    voltage = float(session.read())

                    self.__logger.debug('curr: %f', voltage)

                    self.output.publish(dict(meta=dict(
                            type='answer',
                            answer_type='get_voltage',
                            block=1,
                            voltage=voltage
                    ), data=b''))
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
