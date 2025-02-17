"""Конфигурационный файл для сервера HV."""
from logging import DEBUG as _DEBUG

LOGGER_NAME: str = 'hv_server'
LOG_FILE: str = './hv_server.log'
LOG_LEVEL = _DEBUG

DATA_ROOT: str = './data'

VIRTUAL_MODE: bool = True
VIRTUAL_CHANGE_SPEED: int = 200 # скорость изменения напряжения в виртуальном режиме, В/сек

AGILENT_34401A_GPIB_ADDR: str = 'GPIB::20::INSTR'
FLUKE_5502E_GPIB_ADDR: str = 'GPIB::4::INSTR'

# Коэффициент перевода напряжения с Fluke -> FuG35000
HV_SCALING_COEFFICIENT_A: float = 3500.5048
HV_SCALING_COEFFICIENT_B: float = 1.2632
# Множитель делителя
DIVIDER_FACTOR: float = -4050.65

TCP_INTERFACE_HOST: str = "0.0.0.0"
TCP_INTERFACE_PORT: int = 5555

WEB_INTERFACE_HOST: str = "0.0.0.0"
WEB_INTERFACE_PORT: int = 8080

# переписывание параметров из локального конфига (config_local.py)
try:
    # pylint: disable-next=wildcard-import, import-error
    from config_local import *  # type: ignore  # noqa: F403
except ModuleNotFoundError:
    print("no config_local.py provided")
