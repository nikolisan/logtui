import asyncio
from datetime import datetime
from pathlib import Path

import aiofiles
import pytest
from pytest import TempPathFactory

from tui_log_viewer.cli.mappers import LogEntry
from tui_log_viewer.cli.parser import LogParser

# pyright: ignore[reportUnknownMemberType]

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def log_directory(tmp_path_factory: TempPathFactory) -> Path:
    logs = ["process_1.log", "process_2.log"]
    directory = tmp_path_factory.mktemp("logs")
    for log in logs:
        (directory / log).write_text(
            f"""
            2026-06-24 11:56:57,698 - root - INFO - Log level set to INFO\n
            2026-04-24 11:56:58,003 - {log}.module.function - INFO - Test log entry 1 for {log}\n
            2026-04-24 11:57:12,114 - {log}.module_2.function - INFO - Test log entry 2 for {log}\n
            2026-04-25 17:00:12,108 - {log}.module.function - INFO - Test log entry 3 for {log}\n
            2026-04-25 17:03:12,001 - {log}.module.function - ERROR - Test log entry 4 for {log}\n
               File "C:/temp/file/with/error", line 100, in error_function
                 return multiple(errors)
               File "C:/temp/file/with/originating/error", line 100, in error_function
                 return multiple(errors).traceback()
            TypeError: 'NoneType' is not callable.
            2026-04-25 17:17:12,114 - {log}.module_2.function - INFO - Test log entry 5 for {log}\n
            2026-04-28 13:17:12,114 - {log}.module_2.function - WARNING - Test log entry 6 for {log}\n
            ROGUE LINE.\n
            2026-04-28 14:17:12,114 - {log}.module_2.function - INFO - Test log entry 7 for {log}\n
            """,
            encoding="utf-8",
        )

    return directory


def test_logparser_finds_logs(log_directory: Path):
    parser = LogParser(directory=log_directory)
    assert len(parser.files) == 2
    assert list(parser.files.keys()) == ["process_1", "process_2"]


def test_logparser_selects_log(log_directory: Path):
    parser = LogParser(directory=log_directory)
    _select = "process_1.log"
    parser.selected_log = _select
    selected = parser.selected_log
    assert selected == log_directory / "process_1.log"


def test_logparser_raises_on_invalid_log(log_directory: Path):
    parser = LogParser(directory=log_directory)
    with pytest.raises(FileNotFoundError, match="invalid"):
        parser.selected_log = "invalid.log"
        _selected = parser.selected_log


def test_logparser_raises_on_invalid_log_type(log_directory: Path):
    parser = LogParser(directory=log_directory)
    with pytest.raises(ValueError, match="Log must end with .log"):
        parser.selected_log = "invalid"
        _selected = parser.selected_log


@pytest.mark.asyncio
async def test_logparser_reads_lines_from_end(log_directory: Path):
    _log = "process_1.log"
    _no_lines = 2
    log_path = log_directory / _log
    parser = LogParser(directory=log_directory)
    parser.selected_log = _log
    lines = await parser.parse_lines(lines=_no_lines)
    log_bytes = log_path.read_bytes()
    assert len(lines) == _no_lines
    assert lines[0] == LogEntry(
        timestamp=datetime.strptime(
            "2026-04-28 13:17:12,114", "%Y-%m-%d %H:%M:%S,%f"
        ).astimezone(),
        module=f"{_log}.module_2.function",
        level="WARNING",
        message=f"Test log entry 6 for {_log}",
        start_offset=log_bytes.index(
            f"            2026-04-28 13:17:12,114 - {_log}".encode()
        ),
    )
    assert lines[1] == LogEntry(
        timestamp=datetime.strptime(
            "2026-04-28 14:17:12,114", "%Y-%m-%d %H:%M:%S,%f"
        ).astimezone(),
        module=f"{_log}.module_2.function",
        level="INFO",
        message=f"Test log entry 7 for {_log}",
        start_offset=log_bytes.index(
            f"            2026-04-28 14:17:12,114 - {_log}".encode()
        ),
    )


@pytest.mark.asyncio
async def test_logparser_reads_all_lines_if_less_than_requested(log_directory: Path):
    _log = "process_1.log"
    _no_lines = 100
    parser = LogParser(directory=log_directory)
    parser.selected_log = _log
    lines = await parser.parse_lines(lines=_no_lines)
    assert len(lines) == 8


@pytest.mark.asyncio
async def test_logparser_yields_appended_line(log_directory: Path):
    log_name = "process_1.log"
    log_path = log_directory / log_name
    expected = (
        "2026-04-28 14:18:12,114 - "
        f"{log_name}.module_2.function - INFO - Appended log entry"
    )

    # We need to record the EOF first for the test to run
    parser = LogParser(directory=log_directory)
    parser.selected_log = log_name
    await parser.parse_lines()
    append_offset = log_path.stat().st_size

    async with aiofiles.open(log_path, mode="ab") as file:
        await file.write((expected + "\n").encode("utf-8"))

    follower = parser.fetch_new_line()

    try:
        line = await asyncio.wait_for(anext(follower), timeout=1)
    finally:
        await follower.aclose()

    assert line == LogEntry(
        timestamp=datetime.strptime(
            "2026-04-28 14:18:12,114", "%Y-%m-%d %H:%M:%S,%f"
        ).astimezone(),
        module=f"{log_name}.module_2.function",
        level="INFO",
        message="Appended log entry",
        start_offset=append_offset,
    )
