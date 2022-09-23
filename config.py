"""Конфигурационный файл для сервера HV"""
from logging import DEBUG as _DEBUG

LOGGER_NAME = 'hv_server'
LOG_FILE: str = './hv_server.log'
LOG_LEVEL = _DEBUG

VIRTUAL_MODE = True

AGILENT_34401A_GPIB_ADDR = 'GPIB::20::INSTR'
FLUKE_5502E_GPIB_ADDR = 'GPIB::4::INSTR'

# Коэффициент перевода напряжения с Fluke -> FuG35000
HV_SCALING_COEFFICIENT = 3500.0
# Множитель делителя
DIVIDER_FACTOR = -4051.330

# переписывание параметров из локального конфига (config_local.py)
try:
    # pyright: reportMissingImports=false
    # pylint: disable-next=wildcard-import, import-error
    from config_local import *
except ModuleNotFoundError:
    print("no config_local.py provided")
