import datetime
import os
from logging import getLogger
from pathlib import Path

from config import LOCAL_DB_ROOT, LOGGER_NAME, VIRTUAL_MODE


class DailyTsvWriter:
    """
    Класс для записи временных меток и значений в TSV файл.

    Автоматически создает новый файл при смене суток.
    Имя файла формируется как 'basename/гг-мм-дд.tsv'.
    В каждый новый файл записывается заголовок 'timestamp\tvalue'.
    """

    def __init__(self, sensor_name: str):
        """
        Инициализирует логгер.

        Args:
            basename: Базовый каталог для хранения файлов логов.
                      Может быть строкой или объектом Path.
        """
        # Преобразуем basename в объект Path для удобства работы
        self.base_path = Path(os.path.join(LOCAL_DB_ROOT, sensor_name))

        self.__sensor_name = sensor_name
        self.__logger = getLogger(LOGGER_NAME)  # Инициализация логгера

        # Убедимся, что базовая директория существует при инициализации
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.__logger.error(f"failed to create directory {self.base_path}: {e}")
            raise

    def _get_filepath(self, date_obj: datetime.date) -> Path:
        """Формирует полный путь к файлу для указанной даты."""
        date_str = date_obj.strftime("%y-%m-%d")  # Формат гг-мм-дд
        if VIRTUAL_MODE:
            return self.base_path / f"{date_str}-virtual.tsv"
        else:
            return self.base_path / f"{date_str}.tsv"

    def write(self, val: float):
        """
        Записывает текущую временную метку и значение в соответствующий
        дневной TSV файл.

        Args:
            val: Значение типа float для записи.
        """
        now = datetime.datetime.now()
        today = now.date()

        current_filepath = self._get_filepath(today)

        with open(current_filepath, "a") as data_file:
            need_header = current_filepath.stat().st_size == 0
            if need_header:
                data_file.write(f"timestamp\t{self.__sensor_name}\n")

            timestamp_str = now.time().isoformat()
            line = f"{timestamp_str}\t{val}\n"
            data_file.write(line)

    def __enter__(self):
        """Позволяет использовать класс с оператором 'with'."""
        return self

