import asyncio
from datetime import datetime
from logging import getLogger
import sys

from tqdm import tqdm

sys.path.append('./')

import pyvisa as visa

import csv
from utils.logger import init_logger
from config import AGILENT_34401A_GPIB_ADDR, DIVIDER_FACTOR, FLUKE_5502E_GPIB_ADDR, HV_SCALING_COEFFICIENT, LOGGER_NAME


__voltage = 0

async def agilent_loop():
    try:
        resource_mgr = visa.ResourceManager()
        agilent_gpib = resource_mgr.open_resource(AGILENT_34401A_GPIB_ADDR)

        agilent_gpib.write("*RST")
        await asyncio.sleep(1.0)
        agilent_gpib.write("CONF:VOLT:DC 10,0.00001")
        await asyncio.sleep(1)
        agilent_gpib.write("DET:BAND 3")
        await asyncio.sleep(1)
        agilent_gpib.write("INP:IMP:AUTO ON")
        await asyncio.sleep(1)
        agilent_gpib.write("VOLT:NPLC 100")
        await asyncio.sleep(1)

        with open('voltage.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, dialect="excel")
            while True:
                global __voltage
                agilent_gpib.write('READ?')
                await asyncio.sleep(4)
                __voltage = float(agilent_gpib.read())
                spamwriter.writerow([datetime.now(), __voltage])

    except visa.Error:
        sys.exit() # TODO: change to adequate exit


async def fluke_loop():
    try:
        resource_mgr = visa.ResourceManager()
        fluke_gpib = resource_mgr.open_resource(FLUKE_5502E_GPIB_ADDR)

        fluke_gpib.write("OPER")
        await asyncio.sleep(2)

        with open('voltage_sets.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, dialect="excel")
            with tqdm(range(0, 18000, 1000), total=18) as t:
                for voltage in t:
                    spamwriter.writerow([datetime.now().isoformat(), voltage, voltage / HV_SCALING_COEFFICIENT])
                    fluke_gpib.write(f'OUT {voltage / HV_SCALING_COEFFICIENT} V')
                    for _ in range(180//5):
                        t.set_description(f'{voltage}:{__voltage * DIVIDER_FACTOR}', refresh=True)
                        await asyncio.sleep(5)
    except visa.Error:
        sys.exit() # TODO: change to adequate exit


if __name__ == "__main__":
    init_logger()
    loop = asyncio.new_event_loop()
    agilent_coro = loop.create_task(agilent_loop())
    loop.run_until_complete(fluke_loop())
    agilent_coro.cancel()


