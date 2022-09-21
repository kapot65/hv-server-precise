"""Модуль для работы с аппаратной частью стойки HV."""
import asyncio
import sys
import json
from logging import getLogger

import jsonschema

from config import AGILENT_34401A_GPIB_ADDR, LOGGER_NAME, VIRTUAL_MODE
from utils.manager import HardwareManager

if VIRTUAL_MODE:
    from random import random
else:
    import pyvisa as visa

_logger = getLogger(LOGGER_NAME)

class HVManager(HardwareManager):
    """Менеджер для управления стойкой HV."""

    def __init__(self):
        super().__init__()

        self.__schema = json.load(open("./commands.schema.json"))

        if VIRTUAL_MODE:
            self.__desired_voltage = 0.0
            self.__calc_next_coro = None
        else:
            self.__agilent_gpib = None

        self.last_voltage = 0.0
        
        self.__message_coro =  None
        self.__monitor_coro = None

    async def __init__agilent_34401a(self):
        if VIRTUAL_MODE:
            _logger.debug('Initialize voltmeter in virtual mode')
        else:
            _logger.debug('Initialize Agilent 34401A')
            try:
                # Create a connection (session) to the instrument
                resource_mgr = visa.ResourceManager()
                self.__agilent_gpib = resource_mgr.open_resource(AGILENT_34401A_GPIB_ADDR)
            except visa.Error:
                _logger.error('Couldn\'t connect to \'%s\', exiting now...', AGILENT_34401A_GPIB_ADDR)
                sys.exit() # TODO: change to adequate exit

            _logger.debug("*RST")
            self.__agilent_gpib.write("*RST")
            await asyncio.sleep(1.0)
            _logger.debug("CONF:VOLT:DC 10,0.00001")
            self.__agilent_gpib.write("CONF:VOLT:DC 10,0.00001")
            await asyncio.sleep(1)
            _logger.debug("DET:BAND 3")
            self.__agilent_gpib.write("DET:BAND 3")
            await asyncio.sleep(1)
            # _logger.debug("INP:IMP:AUTO ON")
            # self.__agilent_gpib.write("INP:IMP:AUTO ON")
            # await asyncio.sleep(1)
            _logger.debug("VOLT:NPLC 100")
            self.__agilent_gpib.write("VOLT:NPLC 100")
            await asyncio.sleep(1)

            _logger.debug('Agilent 34401A initialization done')

    async def __stop_agilent_34401a(self):
        if VIRTUAL_MODE:
            _logger.debug('Virtual voltmeter stopped')
        else:
            # TODO: добавить вычитку (чтобы вольтметр не пищал при след. запуске)
            _logger.debug('Agilent 34401A stopped')

    async def __init_fluke_5200e(self):
        if VIRTUAL_MODE:
            _logger.debug('Initialize PS Calibrator in virtual mode')
            async def calc_next_voltage():
                change_speed = 200.0
                while True:
                    await asyncio.sleep(1)
                    sign = 1 if self.__desired_voltage > self.last_voltage else -1
                    delta = abs(self.last_voltage - self.__desired_voltage)
                    self.last_voltage += sign * \
                        min(change_speed, delta) + \
                            (random() - 0.5)
            self.__calc_next_coro = asyncio.create_task(calc_next_voltage())
        else:
            _logger.warning("__init_fluke_5200e is not implemeted for real device")

    async def __stop_fluke_5200e(self):
        if VIRTUAL_MODE:
            if self.__calc_next_coro:
                self.__calc_next_coro.cancel()
                self.__calc_next_coro = None
            _logger.debug('Virtual PS Calibrator stopped')
        else:
            # TODO: добавить вычитку (чтобы вольтметр не пищал при след. запуске)
            _logger.debug('Fluke 5502E stopped')

    async def __set_voltage(self, voltage: float):
        if VIRTUAL_MODE:
            self.__desired_voltage = voltage
        else:
            _logger.warning("set_voltage is not implemeted for real device")

    async def __get_voltage(self) -> float:
        if VIRTUAL_MODE:
            await asyncio.sleep(4)
            return self.last_voltage
        else:
            self.__agilent_gpib.write('READ?')
            await asyncio.sleep(4)
            voltage = float(self.__agilent_gpib.read())
            return voltage

    async def __wait_voltage(self, voltage, max_error):
        while True:
            if abs(self.last_voltage - voltage) <= max_error :
                return
            await asyncio.sleep(1)

    async def __process_message(self):
        while True:
            try:
                message = await self.input.get()
                _logger.debug(message)
                meta = message['meta']
                try:
                    jsonschema.validate(meta, self.__schema)
                    if meta['command_type'] == 'set_voltage':
                        voltage = float(meta['voltage'])
                        _logger.debug('setting %s', voltage)
                        await self.__set_voltage(voltage)
                        self.output.publish(dict(meta=dict(
                            type="answer",
                            answer_type='set_voltage',
                            block="1",
                            status="ok"
                        ), data= b''))
                    elif meta['command_type'] == 'set_voltage_and_check':
                        voltage = float(meta['voltage'])
                        max_error = float(meta['max_error'])
                        timeout_ = float(meta['timeout'])
                        _logger.debug('setting %s', voltage)
                        await self.__set_voltage(voltage)
                        try:
                            await asyncio.wait_for(
                                self.__wait_voltage(
                                    voltage, max_error), timeout=timeout_)
                            self.output.publish(dict(meta=dict(
                                type="answer",
                                answer_type='set_voltage_and_check',
                                block="1",
                                status="ok",
                                voltage=self.last_voltage,
                                error=self.last_voltage - voltage
                            ), data= b''))
                        except asyncio.exceptions.TimeoutError:
                            self.output.publish(dict(meta=dict(
                                type="answer",
                                answer_type='set_voltage_and_check',
                                block="1",
                                status="timeout",
                                voltage=self.last_voltage,
                                error=self.last_voltage - voltage
                            ), data= b''))     
                    else:
                        _logger.debug(meta)
                except jsonschema.ValidationError as err:
                    self.output.publish(dict(meta=dict(
                        type="reply",
                        reply_type="error",
                        error_code=9,
                        description=err.message
                    ), data=b''))
            except asyncio.CancelledError as exc:
                raise exc
            # pylint: disable-next=broad-except
            except Exception as exc:
                _logger.exception(exc)

    async def __monitor_voltage(self):
        while True:
            try:
                while True:
                    voltage = await self.__get_voltage()
                    _logger.debug('curr: %f', voltage)
                    self.last_voltage = voltage
                    self.output.publish(dict(meta=dict(
                            type='answer',
                            answer_type='get_voltage',
                            block=1,
                            voltage=voltage
                    ), data=b''))
            except asyncio.CancelledError as exc:
                raise exc
            # pylint: disable-next=broad-except
            except Exception as exc:
                _logger.exception(exc)

    async def start(self):

        await self.__init__agilent_34401a()
        await self.__init_fluke_5200e()

        self.__message_coro =  asyncio.create_task(self.__process_message())
        self.__monitor_coro = asyncio.create_task(self.__monitor_voltage())

    async def stop(self):
        if self.__message_coro:
            self.__message_coro.cancel()
            self.__message_coro = None

        if self.__monitor_coro:
            self.__monitor_coro.cancel()
            self.__monitor_coro = None

        await self.__stop_agilent_34401a()
        await self.__stop_fluke_5200e()
