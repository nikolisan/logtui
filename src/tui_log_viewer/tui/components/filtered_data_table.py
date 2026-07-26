from collections import deque
from datetime import datetime

from rich.align import Align
from rich.text import Text, TextType
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable

from tui_log_viewer.cli.mappers import LogEntry


def colour_log_level(level: str) -> Text:
    colors = {
        "DEBUG": "italic cyan",
        "INFO": "blue",
        "WARNING": "yellow",
        "WARN": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red",
        "FATAL": "bold red",
    }
    return Text(level, style=colors.get(level.upper(), "white"))


def vertically_center(value: str | Text | TextType, height: int = 3) -> Align:
    return Align(
        value,
        align="left",
        vertical="middle",
        height=height,
    )


def process_timestamp(timestamp: datetime) -> tuple[str, str]:
    date = timestamp.strftime("%d %b %Y")
    time = timestamp.strftime("%H:%M:%S")
    return date, time


class FilteredDataTable(DataTable[Align]):
    class LogEntrySelected(Message):
        def __init__(self, entry: LogEntry, next_entry: LogEntry | None) -> None:
            self.entry = entry
            self.next_entry = next_entry
            super().__init__()

    filter: reactive[str | None] = reactive(None)
    data: reactive[deque[LogEntry] | None] = reactive(None)

    def __init__(self, **kwargs):  # pyright: ignore
        super().__init__(**kwargs)  # pyright: ignore
        self._row_entries: dict[object, LogEntry] = {}

    def _refresh_rows(self) -> None:
        self.clear(columns=False)
        self._row_entries.clear()

        if not self.data:
            return

        filter_text = (self.filter or "").casefold()

        for index, entry in enumerate(self.data):
            if filter_text and filter_text not in entry.level.casefold():
                continue

            date, time = process_timestamp(entry.timestamp)

            row_key = self.add_row(
                vertically_center(Text(date, style="bold grey50")),
                vertically_center(Text(time, style="bold grey50")),
                vertically_center(Text(entry.module, style="italic deep_sky_blue4")),
                vertically_center(colour_log_level(entry.level)),
                vertically_center(entry.message),
                label=vertically_center(str(index + 1)),  # pyright: ignore[reportArgumentType]
                height=3,
            )
            self._row_entries[row_key] = entry

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        entry = self._row_entries.get(event.cell_key.row_key, None)
        if entry is None:
            return

        entries = list(self.data or ())
        entry_index = next(
            (index for index, item in enumerate(entries) if item is entry), None
        )
        next_entry = (
            entries[entry_index + 1]
            if entry_index is not None and entry_index + 1 < len(entries)
            else None
        )

        self.post_message(self.LogEntrySelected(entry, next_entry))

    def watch_data(self, data: deque[LogEntry]) -> None:
        self._refresh_rows()

    def watch_filter(self, fiter_text: str | None) -> None:
        self.notify(f"Filter: {fiter_text}")
        self._refresh_rows()
