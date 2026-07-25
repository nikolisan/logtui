import textwrap

from tui_log_viewer.cli.mappers import LogEntry


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
        + f"{textwrap.shorten(module, 50):<50} | "
        + f"{textwrap.shorten(level, 7):<7} | "
        + f"{textwrap.shorten(message, 50):<50}"
    )
