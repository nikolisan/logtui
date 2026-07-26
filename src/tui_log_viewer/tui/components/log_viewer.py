from collections import deque
from pathlib import Path
from typing import cast

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive, var
from textual.widgets import Button, Select, Static, Switch
from textual.worker import Worker

from tui_log_viewer.cli import LogParser
from tui_log_viewer.cli.mappers import LogEntry
from tui_log_viewer.tui.components import FilteredDataTable, LabeledSwitch
from tui_log_viewer.tui.Screens import LogEntryModalScreen


class LogViewerComponent(Container):
    DEFAULT_CSS = """
        LogViewerComponent {
            margin: 1 0 0 0;
            padding: 0 1;
            border: round $accent 80%;
            border-title-align: center;
            layout: grid;
            grid-size: 2;
            grid-columns: 1fr 1fr;
            grid-rows: 10% 90%;
        }
        Button {
            margin: 0 1;
        }
        .box {
            height: 100%;
        }
        #two {
            column-span: 2;
        }
        #table {
            background: transparent;
        }
        .datatable--odd-row {
            background: $foreground 5%;
        }

    """

    COLUMNS = ("Date", "Time", "Module", "Level", "Message")
    FILTER = ("debug", "info", "warning", "error", "fatal")
    _file_path: var[Path] = var(Path(""), init=False)
    _parser: var[LogParser | None] = var(None)
    _selected_log: reactive[str | None] = reactive(None)
    _follow_worker: Worker[None] | None = None

    def compose(self) -> ComposeResult:
        yield Horizontal(
            LabeledSwitch(text="Follow"),
            Button("Clear", id="clear-log", variant="warning"),
            Button("Reload", id="reload-log"),
            Select[str](
                ((line.upper(), line) for line in self.FILTER),
                allow_blank=True,
            ),
            classes="box",
        )
        yield Static("", classes="box")
        yield Container(
            FilteredDataTable(zebra_stripes=True, id="table"), classes="box", id="two"
        )

    def on_mount(self) -> None:
        table = self.query_one(FilteredDataTable)
        for col in self.COLUMNS:
            table.add_column(col, key=col)

    def _move_to_end(self):
        table = self.query_one(FilteredDataTable)
        table.move_cursor(row=table.row_count - 1)
        table.call_after_refresh(table.scroll_end, animate=True)

    def _retrieve_log(self, log_name: str) -> None:
        if self._parser is None:
            return

        if self._parser.directory.resolve() == self._file_path.parent.resolve():
            self._parser.selected_log = log_name
            self.notify(f"Selected log: {log_name}")
            self.run_worker(self._parse_log_lines(lines=100))

    # --- Parsers ---- #
    async def _parse_log_lines(self, lines: int = 10) -> None:
        if self._parser is None:
            return
        parsed: deque[LogEntry] = await self._parser.parse_lines(lines=lines)
        if parsed:
            table = self.query_one(FilteredDataTable)
            table.data = parsed
            self._move_to_end()

    async def _follow_log(self) -> None:
        if self._parser is None:
            return

        async for entry in self._parser.fetch_new_line():
            table = self.query_one(FilteredDataTable)
            current = table.data or deque(maxlen=100)
            updated = deque(current, maxlen=100)
            updated.append(entry)
            table.data = updated
            self._move_to_end()

    def _start_following(self) -> None:
        if self._parser is None or self._parser.selected_log is None:
            self.notify("Select a log before following it")
            self.query_one(LabeledSwitch).value = False
            return

        self._stop_following()
        self._follow_worker = self.run_worker(
            self._follow_log(),
            name="follow-log",
            group="follow-log",
            exclusive=True,
        )

    def _stop_following(self) -> None:
        if self._follow_worker is not None:
            self._follow_worker.cancel()
            self._follow_worker = None

    def watch__file_path(self, path: Path):
        if path.is_file():
            self.border_title = path.name
            self._retrieve_log(path.name)
        else:
            self.border_title = ""

    def watch__parser(self, old_parser: LogParser, parser: LogParser) -> None:
        if self._parser is None:
            return
        if self._file_path:
            self._retrieve_log(self._file_path.name)

    @on(Switch.Changed)
    def follow_changed(self, event: Switch.Changed) -> None:
        if event.value:
            self._start_following()
        else:
            self._stop_following()

    @on(Button.Pressed, "#clear-log")
    def clear_log(self) -> None:
        self.query_one(FilteredDataTable).data = None

    @on(Button.Pressed, "#reload-log")
    def reload_log(self) -> None:
        self.notify("Reload...")
        self._retrieve_log(self._file_path.name)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        table = self.query_one(FilteredDataTable)
        table.filter = event.value if isinstance(event.value, str) else None
        self._move_to_end()

    @on(FilteredDataTable.LogEntrySelected)
    def show_log_entry(self, event: FilteredDataTable.LogEntrySelected) -> None:
        if not self._file_path.is_file():
            self.notify("No log file is selected", severity="error", timeout=3)
            return
        app = cast(App[None], self.app)  # pyright: ignore[reportUnknownMemberType]
        app.push_screen(
            LogEntryModalScreen(self._file_path, event.entry, event.next_entry),
        )
