import datetime
import os
from logging import getLogger
from pathlib import Path

from config import LOCAL_DB_ROOT, LOGGER_NAME


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
        self.current_date = None
        self.file_handle = None
        self.current_filepath = None

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

        # Проверяем, изменилась ли дата с последней записи
        if today != self.current_date:
            # Дата изменилась (или это первая запись)
            if self.file_handle:
                # Закрываем старый файл, если он был открыт
                try:
                    self.file_handle.close()
                except IOError as e:
                    self.__logger.error(f"closing {self.current_filepath} failed: {e}")
                self.file_handle = None

            # Обновляем текущую дату и путь к файлу
            self.current_date = today
            self.current_filepath = self._get_filepath(today)

            # Открываем новый файл в режиме добавления ('a').
            # Файл будет создан, если не существует.
            # Используем utf-8 кодировку.
            try:
                # Проверяем, существует ли файл и пуст ли он, чтобы решить, нужен ли заголовок
                needs_header = (
                    not self.current_filepath.exists()
                    or self.current_filepath.stat().st_size == 0
                )

                self.file_handle = open(self.current_filepath, "a", encoding="utf-8")

                if needs_header:
                    self.file_handle.write(f"timestamp\t{self.__sensor_name}\n")
                    self.file_handle.flush()  # Сбросим буфер после заголовка

            except IOError as e:
                self.__logger.error(
                    f"failed to open/write header to{self.current_filepath}: {e}"
                )
                self.file_handle = None  # Не удалось открыть файл
                self.current_date = (
                    None  # Сбросить дату, чтобы попытаться снова при следующем вызове
                )
                return  # Прекращаем выполнение метода, если файл не открылся

        # Если файл не открыт (например, из-за ошибки выше), выходим
        if not self.file_handle:
            self.__logger.error(
                f"File handle is None, cannot write to {self.current_filepath}"
            )
            return

        # Формируем строку для записи
        # Используем формат ISO 8601 для временной метки для универсальности
        timestamp_str = now.time().isoformat()
        line = f"{timestamp_str}\t{val}\n"

        # Записываем строку в файл и сбрасываем буфер
        try:
            self.file_handle.write(line)
            self.file_handle.flush()  # Гарантирует запись данных на диск
        except IOError as e:
            self.__logger.error(f"failed to write row to {self.current_filepath}: {e}")
            # Попытка закрыть файл при ошибке записи
            self.close()
            self.current_date = None  # Сбросить дату для повторной попытки открытия

    def close(self):
        """Закрывает текущий открытый файл лога."""
        if self.file_handle:
            try:
                self.file_handle.close()
                print(f"Файл {self.current_filepath} закрыт.")
            except IOError as e:
                print(f"Ошибка при закрытии файла {self.current_filepath}: {e}")
            self.file_handle = None
        self.current_date = None  # Сбрасываем дату при закрытии

    def __del__(self):
        """Гарантирует закрытие файла при удалении объекта сборщиком мусора."""
        # print("Вызван __del__, закрытие файла...") # Для отладки
        self.close()

    def __enter__(self):
        """Позволяет использовать класс с оператором 'with'."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Гарантирует закрытие файла при выходе из блока 'with'."""
        # print("Вызван __exit__, закрытие файла...") # Для отладки
        self.close()
