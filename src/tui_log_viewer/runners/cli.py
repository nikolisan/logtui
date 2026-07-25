import argparse
import asyncio
import logging

from tui_log_viewer.cli import LogParser
from tui_log_viewer.cli.tools import printer, printer_header
from tui_log_viewer.runners.arg_parser import parse_arguments

logger = logging.getLogger(__name__)


async def start_cli_no_tui(args: argparse.Namespace):
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
    except Exception as e:
        logger.exception(f"{type(e).__name__}: {e}")  # noqa: TRY401


if __name__ == "__main__":
    print("This module should not be imported")
    raise ImportError("logtui.runners.cli is not importable")
