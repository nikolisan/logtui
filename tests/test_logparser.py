import asyncio
from pathlib import Path

import aiofiles
import pytest

from tui_log_viewer.cli.parser import LogParser

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def log_directory(tmp_path_factory) -> Path:
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


def test_logparser_finds_logs(log_directory):
    parser = LogParser(directory=log_directory)
    assert len(parser.files) == 2
    assert list(parser.files.keys()) == ["process_1", "process_2"]


def test_logparser_selects_log(log_directory):
    parser = LogParser(directory=log_directory)
    _select = "process_1.log"
    parser.selected_log = _select
    selected = parser.selected_log
    assert selected == log_directory / "process_1.log"


def test_logparser_raises_on_invalid_log(log_directory):
    parser = LogParser(directory=log_directory)
    with pytest.raises(FileNotFoundError, match="invalid"):
        parser.selected_log = "invalid.log"
        _selected = parser.selected_log


def test_logparser_raises_on_invalid_log_type(log_directory):
    parser = LogParser(directory=log_directory)
    with pytest.raises(ValueError, match="Log must end with .log"):
        parser.selected_log = "invalid"
        _selected = parser.selected_log


@pytest.mark.asyncio
async def test_logparse_parse_lines_raises_value_error(log_directory):
    parser = LogParser(directory=log_directory)
    parser.selected_log = "process_1.log"
    with pytest.raises(TypeError, match="must be an integer"):
        assert await parser.parse_lines(lines="invalid_type")


@pytest.mark.asyncio
async def test_logparser_reads_lines_from_end(log_directory):
    _log = "process_1.log"
    _no_lines = 2
    parser = LogParser(directory=log_directory)
    parser.selected_log = _log
    lines = await parser.parse_lines(lines=_no_lines)
    assert len(lines) == _no_lines
    assert (
        lines[0]
        == f"2026-04-28 13:17:12,114 - {_log}.module_2.function - WARNING - Test log entry 6 for {_log}"
    )
    assert (
        lines[1]
        == f"2026-04-28 14:17:12,114 - {_log}.module_2.function - INFO - Test log entry 7 for {_log}"
    )


@pytest.mark.asyncio
async def test_logparser_reads_all_lines_if_less_than_requested(log_directory):
    _log = "process_1.log"
    _no_lines = 100
    parser = LogParser(directory=log_directory)
    parser.selected_log = _log
    lines = await parser.parse_lines(lines=_no_lines)
    assert len(lines) == 8


@pytest.mark.asyncio
async def test_logparser_yields_appended_line(log_directory):
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

    async with aiofiles.open(log_path, mode="ab") as file:
        await file.write((expected + "\n").encode("utf-8"))

    follower = parser.fetch_new_line()

    try:
        line = await asyncio.wait_for(anext(follower), timeout=1)
    finally:
        await follower.aclose()

    assert line == expected
