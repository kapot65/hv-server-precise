"""Модуль для работы с аппаратной частью стойки HV."""

import asyncio
import json
import sys
from logging import getLogger
from typing import Optional

import jsonschema

from config import (
    AGILENT_34401A_GPIB_ADDR as AGILENT_ADDR,
)
from config import (
    DIVIDER_FACTOR,
    LOGGER_NAME,
    VIRTUAL_CHANGE_SPEED,
    VIRTUAL_MODE,
)
from config import (
    FLUKE_5502E_GPIB_ADDR as FLUKE_ADDR,
)
from db import DailyTsvWriter
from utils.manager import HardwareManager
from utils.scale import rescale_voltage as scale

if VIRTUAL_MODE:
    from random import random
else:
    import pyvisa as visa

_logger = getLogger(LOGGER_NAME)


class HVManager(HardwareManager):
    """Менеджер для управления стойкой HV."""

    def __init__(self, db_writer: Optional[DailyTsvWriter] = None):
        """Инициализация менеджера."""
        super().__init__()

        self.__db_writer = db_writer
        self.__schema = json.load(open("./commands.schema.json"))

        if VIRTUAL_MODE:
            self.__V_set = 0.0
            self.__calc_next_coro = None
        else:
            self.__visa_mgr = visa.ResourceManager()
            self.__agilent = None
            self.__fluke = None

        self.V_last = 0.0

        self.__cmd_coro = None

        self.__handle_input_coro = None
        self.__monitor_coro = None

    async def __init__agilent_34401a(self):
        if VIRTUAL_MODE:
            _logger.debug("Initialize voltmeter in virtual mode")
        else:
            _logger.debug("Initialize Agilent 34401A")
            try:
                self.__agilent = self.__visa_mgr.open_resource(AGILENT_ADDR)
            except visa.Error:
                _logger.error("Couldn't connect to '%s', exiting now...", AGILENT_ADDR)
                sys.exit()  # TODO: change to adequate exit

            _logger.debug("*RST")
            self.__agilent.write("*RST")  # type: ignore
            await asyncio.sleep(1.0)
            _logger.debug("CONF:VOLT:DC 10,0.00001")
            self.__agilent.write(  # type: ignore
                "CONF:VOLT:DC 10,0.00001"
            )
            await asyncio.sleep(1)
            _logger.debug("DET:BAND 3")
            self.__agilent.write("DET:BAND 3")  # type: ignore
            await asyncio.sleep(1)
            _logger.debug("INP:IMP:AUTO ON")
            self.__agilent.write("INP:IMP:AUTO ON")  # type: ignore
            await asyncio.sleep(1)
            _logger.debug("VOLT:NPLC 100")
            self.__agilent.write("VOLT:NPLC 100")  # type: ignore
            await asyncio.sleep(1)

            _logger.debug("Agilent 34401A initialization done")

    async def __stop_agilent_34401a(self):
        if VIRTUAL_MODE:
            _logger.debug("Virtual voltmeter stopped")
        else:
            self.__agilent.read()  # type: ignore
            _logger.debug("Agilent 34401A stopped")

    async def __init_fluke_5200e(self):
        if VIRTUAL_MODE:
            _logger.debug("Initialize PS Calibrator in virtual mode")

            async def calc_next_voltage():
                while True:
                    await asyncio.sleep(1)
                    sign = 1 if self.__V_set > self.V_last else -1
                    delta = abs(self.V_last - self.__V_set)
                    self.V_last += sign * min(VIRTUAL_CHANGE_SPEED, delta) + (
                        random() - 0.5
                    )

            self.__calc_next_coro = asyncio.create_task(calc_next_voltage())
        else:
            _logger.debug("Initialize Fluke 5502E")
            try:
                self.__fluke = self.__visa_mgr.open_resource(FLUKE_ADDR)
            except visa.Error:
                _logger.error("Couldn't connect to '%s', exiting now...", FLUKE_ADDR)
                sys.exit()  # TODO: change to adequate exit

            _logger.debug("OPER")
            self.__fluke.write("OPER")  # type: ignore
            await asyncio.sleep(2)

            _logger.debug("Fluke 5502E initialization done")

    async def __stop_fluke_5200e(self):
        if VIRTUAL_MODE:
            if self.__calc_next_coro:
                self.__calc_next_coro.cancel()
                self.__calc_next_coro = None
            _logger.debug("Virtual PS Calibrator stopped")
        else:
            # TODO: добавить вычитку(чтобы вольтметр не пищал при перезапуске)
            _logger.debug("Fluke 5502E stopped")

    async def __set_voltage(self, voltage: float):
        if VIRTUAL_MODE:
            self.__V_set = voltage
            await asyncio.sleep(2)
        else:
            self.__fluke.write(f"OUT {scale(voltage)} V")  # type: ignore
            await asyncio.sleep(2)

    async def __get_voltage(self) -> float:
        if VIRTUAL_MODE:
            await asyncio.sleep(4)
            return self.V_last
        else:
            self.__agilent.write("READ?")  # type: ignore
            await asyncio.sleep(4)
            voltage = float(self.__agilent.read())  # type: ignore
            return voltage * DIVIDER_FACTOR

    async def __wait_voltage(self, voltage, max_error):
        while True:
            if abs(self.V_last - voltage) <= max_error:
                return
            await asyncio.sleep(1)

    async def __process_single_command(self, meta: dict):
        if meta["command_type"] == "set_voltage":
            voltage = float(meta["voltage"])
            _logger.debug("setting %s", voltage)
            await self.__set_voltage(voltage)
            self.output.publish(
                dict(
                    meta=dict(
                        type="answer", answer_type="set_voltage", block="1", status="ok"
                    ),
                    data=b"",
                )
            )
        elif meta["command_type"] == "set_voltage_and_check":
            voltage = float(meta["voltage"])
            max_error = float(meta["max_error"])
            timeout_ = float(meta["timeout"])
            _logger.debug("setting %s", voltage)
            await self.__set_voltage(voltage)
            try:
                await asyncio.wait_for(
                    self.__wait_voltage(voltage, max_error), timeout=timeout_
                )
                self.output.publish(
                    dict(
                        meta=dict(
                            type="answer",
                            answer_type="set_voltage_and_check",
                            block="1",
                            status="ok",
                            voltage=self.V_last,
                            error=self.V_last - voltage,
                        ),
                        data=b"",
                    )
                )
            except asyncio.exceptions.TimeoutError:
                self.output.publish(
                    dict(
                        meta=dict(
                            type="answer",
                            answer_type="set_voltage_and_check",
                            block="1",
                            status="timeout",
                            voltage=self.V_last,
                            error=self.V_last - voltage,
                        ),
                        data=b"",
                    )
                )
        else:
            _logger.debug(meta)

    async def __handle_input(self):
        """Обработка сообщений из входящего потока.

        В этом методе происходит базовая обработка.
        - SERVER_BUSY_ERROR (приход новой команды во время обработки)
        - INCORRECT_MESSAGE_PARAMS (некорректная команда)
        - ALGORITM_ERROR (Exception при выполнении команды)
        Обработка команд производится в методе :meth:`__process_single_command`
        """
        while True:
            try:
                message = await self.input.get()
                _logger.debug(message)
                meta = message["meta"]
                try:
                    jsonschema.validate(meta, self.__schema)
                    if self.__cmd_coro is None or self.__cmd_coro.done():
                        temp_coro = self.__cmd_coro
                        self.__cmd_coro = asyncio.create_task(
                            self.__process_single_command(meta)
                        )
                        if temp_coro is not None:
                            exc = temp_coro.exception()
                            if exc:
                                raise exc
                    else:
                        self.output.publish(
                            dict(
                                meta=dict(
                                    type="reply",
                                    reply_type="error",
                                    error_code=8,
                                    error_text_code="SERVER_BUSY_ERROR",
                                    description="HV server is busy",
                                ),
                                data=b"",
                            )
                        )
                except jsonschema.ValidationError as err:
                    self.output.publish(
                        dict(
                            meta=dict(
                                type="reply",
                                reply_type="error",
                                error_code=9,
                                error_text_code="INCORRECT_MESSAGE_PARAMS",
                                description=err.message,
                            ),
                            data=b"",
                        )
                    )
            except asyncio.CancelledError as exc:
                raise exc
            # pylint: disable-next=broad-except
            except Exception as exc:
                self.output.publish(
                    dict(
                        meta=dict(
                            type="reply",
                            reply_type="error",
                            error_code=5,
                            error_text_code="ALGORITM_ERROR",
                            description=repr(exc),
                        ),
                        data=b"",
                    )
                )
                _logger.exception(exc)

    async def __monitor_voltage(self):
        while True:
            try:
                while True:
                    voltage = await self.__get_voltage()
                    _logger.debug("curr: %f", voltage)
                    self.V_last = voltage
                    if self.__db_writer is not None:
                        self.__db_writer.write(float("{:.2f}".format(voltage)))
                    self.output.publish(
                        dict(
                            meta=dict(
                                type="answer",
                                answer_type="get_voltage",
                                block=1,
                                voltage=voltage,
                            ),
                            data=b"",
                        )
                    )
            except asyncio.CancelledError as exc:
                raise exc
            # pylint: disable-next=broad-except
            except Exception as exc:
                self.output.publish(
                    dict(
                        meta=dict(
                            type="reply",
                            reply_type="error",
                            error_code=5,
                            error_text_code="ALGORITM_ERROR",
                            description=repr(exc),
                        ),
                        data=b"",
                    )
                )
                _logger.exception(exc)

    async def start(self):
        await self.__init__agilent_34401a()
        await self.__init_fluke_5200e()
        self.__handle_input_coro = asyncio.create_task(self.__handle_input())
        self.__monitor_coro = asyncio.create_task(self.__monitor_voltage())

    async def stop(self):
        if self.__handle_input_coro:
            self.__handle_input_coro.cancel()
            self.__handle_input_coro = None
        if self.__monitor_coro:
            self.__monitor_coro.cancel()
            self.__monitor_coro = None
        await self.__stop_agilent_34401a()
        await self.__stop_fluke_5200e()
