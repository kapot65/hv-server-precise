"""Hardware manager abstract class."""
import asyncio

from utils.hub import Hub


class HardwareManager():
    """Class for hardware logic class."""

    def __init__(self):
        self._input = asyncio.Queue()
        self._output = Hub()

    @property
    def input(self):
        """Input messages Query.

        The query record must has type {'meta': dict, 'data': bytes}.
        """
        return self._input

    @property
    def output(self):
        """Output messages Hub.

        The hub record must has type {'meta': dict, 'data': bytes}.
        """
        return self._output

    async def start(self):
        """Called on server starts.

        This method should contains initialization and processing routine logic.
        """
        raise NotImplementedError(f'define method start in {self.__class__.__name__}')

    async def stop(self):
        """Called on server shutdown.

        This method should contains logic for graceful shutdown.
        """
        raise NotImplementedError(f'define method stop in {self.__class__.__name__}')
