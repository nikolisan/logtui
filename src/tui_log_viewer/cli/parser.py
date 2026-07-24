import asyncio
import logging
import os
import re
from collections import deque
from collections.abc import AsyncGenerator
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


def _parse_line(line: str) -> str | None:
    """Regex match of line to ensure it starts with YYYY-MM-DD HH:MM:SS:mss"""
    _pattern = r"^((?:19|20)[0-9][0-9])-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]) (?:[01][0-9]|2[03]):([0-5][0-9]):([0-5][0-9]),([0-9]{3}) - "
    if not re.match(_pattern, line.strip()):
        return None
    else:
        return line.strip()


class LogParser:
    def __init__(self, directory: str | Path):
        self._directory = Path(directory)
        self._files: dict[str, Path] = self.retrieve_files()
        self._selected_log: Path | None = None
        self._last_position: int | None = None

    @property
    def files(self) -> dict[str, Path]:
        return self._files

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def selected_log(self):
        return self._selected_log

    @selected_log.setter
    def selected_log(self, log: str | None):
        """
        Set the selected log file
        :param log: the log file in the format of xxx.log
        :raises ValueError: If no log file is selected.
        :raises ValueError: If the log file has incorrect extension
        :raises FileNotFoundError: If the log file does not exist
        """

        if log is None:
            self._selected_log = None
            raise ValueError("No log file is selected")

        if not log.endswith(".log"):
            raise ValueError(f"Log must end with .log: {log}")

        log = log.split(".log")[0]
        _log = self.files.get(log, None)
        if _log:
            self._selected_log = _log
        else:
            raise FileNotFoundError(log)

    def retrieve_files(self) -> dict[str, Path]:
        _found = {}
        for file in self._directory.rglob("*.log"):
            _found[file.stem] = file
        return _found

    async def parse_lines(self, lines: int = 10, buffer_size: int = 2048) -> deque[str]:
        """
        Asynchronously reads the most recent lines from the selected log file ordered from oldest to newest.
        The method allows for 1 to 100 lines to be returned.

        The file is read backwards in chunks of up to buffer_size bytes.
        Lines are decoded as UTF-8, replacing invalid byte sequences.
        If decoded lines are valid log lines, they are stored in a deque.

        :param lines: Maximum number of complete matching lines to return
        :param buffer_size: Maximum number of bytes to read per chunk
        :return: A queue of decoded log lines in oldest to newest order
        :raises ValueError: If no log file has been selected.
        """

        if not isinstance(lines, int):
            raise TypeError("`lines` argument must be an integer")

        _log = self.selected_log
        if _log is None:
            raise ValueError("No log file is selected")

        _no_lines = max(1, min(lines, 100))
        _log_lines: deque[str] = deque(maxlen=_no_lines)

        async with aiofiles.open(_log, "rb") as f:
            await f.seek(0, os.SEEK_END)
            # find the position of the end of the file
            pointer = await f.tell()
            # record the end of file position before traversing the file
            self._last_position = pointer
            buffer = b""
            encountered = 0
            while pointer > 0 and encountered < _no_lines:
                # ensure that we don't read more bytes than left in the file
                # for example pointer=500bytes (left to the start of the file)
                # -> we only read this amount of bytes
                read_size = min(buffer_size, pointer)
                pointer -= read_size
                await f.seek(pointer)
                # Append to stored incomplete lines the new chunk
                buffer = await f.read(read_size) + buffer
                _lines = buffer.split(b"\n")
                # Store incomplete lines for next pass
                buffer = _lines.pop(0)

                for line in reversed(_lines):
                    decoded = _parse_line(line.decode("utf-8", errors="replace"))
                    if decoded:
                        _log_lines.appendleft(decoded)
                        encountered += 1
                        if encountered == _no_lines:
                            return _log_lines

        if buffer and encountered < _no_lines:
            decoded = _parse_line(buffer.decode("utf-8", errors="replace"))
            if decoded:
                _log_lines.appendleft(decoded)

        return _log_lines

    async def fetch_new_line(self, interval: float = 0.5) -> AsyncGenerator[str, None]:
        """Asynchronously follow the log file and yield valid log lines.
        Starts reading at the end of the log file and continues polling for new complete lines
        at the specified interval. Partial lines remain unread.

        :param interval: Interval between reading new lines.
        :yields: Decoded and validated log lines.
        :raises ValueError: If no log file has been selected.
        """
        _log = self.selected_log
        if _log is None:
            raise ValueError("No log file is selected")

        if self._last_position is None:
            _position = 0
            _end = os.SEEK_END
        else:
            _position = self._last_position
            _end = os.SEEK_SET

        async with aiofiles.open(_log, mode="rb") as f:
            await f.seek(_position, _end)
            while True:
                pointer = await f.tell()
                line = await f.readline()
                if not line or not line.endswith(b"\n"):
                    await f.seek(pointer)
                    await asyncio.sleep(interval)
                    continue

                parsed_line = _parse_line(line.decode("utf-8", errors="replace"))
                if parsed_line:
                    yield parsed_line
