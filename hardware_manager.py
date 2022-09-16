"""Модуль для работы с аппаратной частью стойки HV
"""
# TODO: переделать в класс

import asyncio
import sys

import pyvisa as visa

from utils.hub import Hub

INPUT = asyncio.Queue()

OUTPUT = Hub()

HARDWARE_PROCESSES = []

async def routine():
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

    VISA_ADDRESS = 'GPIB::20::INSTR'
    COEFF = 1e6

    try:
        # Create a connection (session) to the instrument
        resourceManager = visa.ResourceManager()
        session = resourceManager.open_resource(VISA_ADDRESS)
    except visa.Error as ex:
        print('Couldn\'t connect to \'%s\', exiting now...' % VISA_ADDRESS)
        sys.exit() # TODO: change to adequate exit


    print("*RST")
    session.write("*RST")
    await asyncio.sleep(1.0)
    print("CONF:VOLT:DC 10,0.00001")
    session.write("CONF:VOLT:DC 10,0.00001")
    await asyncio.sleep(1)
    # print("DET:BAND 3")
    # session.write("DET:BAND 3")
    # await asyncio.sleep(1)
    # print("INP:IMP:AUTO ON")
    # session.write("INP:IMP:AUTO ON")
    # await asyncio.sleep(1)
    # print("VOLT:NPLC 100")
    # session.write("VOLT:NPLC 100")
    # await asyncio.sleep(1)

    print('voltmeter initialization done')

    while True:

        session.write('READ?')
        await asyncio.sleep(4)
        voltage = float(session.read())

        print(f'curr: {voltage}')

        OUTPUT.publish(dict(meta=dict(
                type='answer',
                answer_type='get_voltage',
                block=1,
                voltage=voltage
        ), data=b''))
