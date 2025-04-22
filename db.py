import datetime
import logging
import os

from config import LOCAL_DB_ROOT

class TSVDBWriter:
    """Класс, использующий переделанный [logging.Logger] для записи в TSV файлы с ежедневным ротацией."""
    class __DailyRotatingTSVHandler(logging.FileHandler):
        def __init__(
            self, control_name: str, baseFilename, mode="a", encoding=None, delay=False
        ):
            self._control_name = control_name

            self.baseFilename = baseFilename
            self.current_day = datetime.date.today()

            self.filename = self._get_filename()
            self._write_header_if_new_file()
            logging.FileHandler.__init__(self, self.filename, mode, encoding, delay)

        def _get_filename(self):
            return os.path.join(
                self.baseFilename, f"{self.current_day.strftime('%y-%m-%d')}.tsv"
            )

        def _write_header_if_new_file(self):
            if not os.path.exists(self.filename):
                with open(self.filename, "w") as f:
                    f.write(f"Timestamp\t{self._control_name}\n")

        def emit(self, record):
            try:
                if datetime.date.today() > self.current_day:
                    self.stream.close()
                    self.current_day = datetime.date.today()
                    self.filename = self._get_filename()
                    self._write_header_if_new_file()
                    self.stream = self._open()
                msg = self.format(record)
                self.stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    class __TSVFormatter(logging.Formatter):
        def format(self, record):
            timestamp = datetime.datetime.fromtimestamp(record.created).time().isoformat()
            return f"{timestamp}\t{record.getMessage()}"

    def __init__(self, control_name: str = "HV") -> None:
        # prepare local storage
        control_path = os.path.join(LOCAL_DB_ROOT, control_name)
        os.makedirs(control_path, exist_ok=True)

        logger = logging.getLogger(f"${control_name}-timeseries")
        logger.setLevel(logging.INFO)

        handler = TSVDBWriter.__DailyRotatingTSVHandler(control_name, control_path)
        formatter = TSVDBWriter.__TSVFormatter()
        handler.setFormatter(formatter)

        logger.addHandler(handler)

        self._logger = logger

    def write(self, value: float) -> None:
        self._logger.info(value)
