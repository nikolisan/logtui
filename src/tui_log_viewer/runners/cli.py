import asyncio
import logging
import textwrap

from tui_log_viewer.cli import LogParser
from tui_log_viewer.cli.mappers import LogEntry
from tui_log_viewer.runners.arg_parser import parse_arguments

logger = logging.getLogger(__name__)


def printer_header(directory: str):
    print(f"logtui: Follow log entries at {directory}\n")
    print(f"{'Timestamp':19} | {'Module':50} | {'Level':7} | {'Message':50}")
    print(f"{'-' * 19} + {'-' * 50} + {'-' * 7} + {'-' * 50}")


def printer(entry: LogEntry):
    timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    module = entry.module
    level = entry.level
    message = entry.message

    print(
        f"{timestamp:19} | "
        f"{textwrap.shorten(module, 50):<50} | "
        f"{textwrap.shorten(level, 7):<7} | "
        f"{textwrap.shorten(message, 50):<50}"
    )


async def start_cli_no_tui(args):
    logger.info("Starting CLI without TUI")
    printer_header(args.INPUT.parent)
    log_parser = LogParser(args.INPUT.parent)
    log_parser.selected_log = args.INPUT.name
    lines = await log_parser.parse_lines(args.n)
    for line in lines:
        printer(line)
    if args.follow:
        follow_generator = log_parser.fetch_new_line()
        try:
            async for new_line in follow_generator:
                printer(new_line)
        finally:
            await follow_generator.aclose()


def main():
    args = parse_arguments()
    try:
        if args.engine == "log":
            asyncio.run(start_cli_no_tui(args))
    except KeyboardInterrupt:
        logger.info("Stopped following log file")
    except Exception:
        logger.exception("Unhandled exception in CLI.")


if __name__ == "__main__":
    print("This module should not be imported")
    raise ImportError("logtui.runners.cli is not importable")
