import textwrap

from tui_log_viewer.cli.mappers import LogEntry
from tui_log_viewer.utils.colour import Coloured


def printer_header(directory: str) -> None:
    print(f"logtui: Follow log entries at {directory}\n")
    print(f"{'Timestamp':20} | {'Module':70} | {'Level':10} | {'Message':70}")
    print(f"{'-' * 20} + {'-' * 70} + {'-' * 10} + {'-' * 70}")


def printer(entry: LogEntry) -> None:
    timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    module = textwrap.shorten(entry.module, width=70, placeholder="...")
    level = textwrap.shorten(entry.level, width=10, placeholder="...")
    message = textwrap.shorten(entry.message, width=70, placeholder="...")

    timestamp_field = f"{timestamp:<20}"
    module_field = f"{module:<70}"
    level_field = f"{level:<10}"
    message_field = f"{message:<70}"

    module_field = Coloured.BLUE(module_field)
    level_field = Coloured.for_level(
        level_field,
        entry.level,
        bold=True,
    )

    print(f"{timestamp_field} | {module_field} | {level_field} | {message_field}")
