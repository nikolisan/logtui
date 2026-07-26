from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Label, TextArea
from textual.worker import Worker

from tui_log_viewer.cli.mappers import LogEntry


class LogEntryModalScreen(ModalScreen[None]):
    DEFAULT_CSS = """
    LogEntryModalScreen {
        align: center middle;
    }

    #dialog {
        width: 70%;
        height: 70%;
        border: round $primary 80%;
        padding: 1;
    }

    #title {
        height: auto;
        margin-bottom: 1;
    }

    #content {
        height: 1fr;
    }
    """

    BINDINGS: ClassVar = [("escape", "close", "Close"), ("q", "close", "Close")]

    def __init__(
        self,
        log_path: Path,
        entry: LogEntry,
        next_entry: LogEntry | None,
    ) -> None:
        super().__init__()
        self.log_path = log_path
        self.entry = entry
        self.next_entry = next_entry
        self._read_entry_worker: Worker[str] | None = None

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Loading log entry...", id="title"),
            TextArea("", read_only=True, id="content"),
            id="dialog",
        )
        yield Footer(show_command_palette=False, compact=True)

    def on_mount(self) -> None:
        self._read_entry_worker = self.run_worker(
            self._read_entry,
            name="read-log-entry",
            thread=True,
        )

    def _read_entry(self) -> str:
        start = self.entry.start_offset
        end = (
            self.next_entry.start_offset
            if self.next_entry is not None
            else self.log_path.stat().st_size
        )

        if end < start:
            raise ValueError(f"Invalid log offsets: {start}..{end}")

        with self.log_path.open("rb") as log_file:
            log_file.seek(start)
            content = log_file.read(end - start)

        return content.decode("utf-8", errors="replace")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        worker = self._read_entry_worker
        if worker is None or event.worker is not worker:  # pyright: ignore[reportUnknownMemberType]
            return

        if event.state.name == "SUCCESS":
            self.query_one(TextArea).load_text(worker.result or "")
            self.query_one("#title", Label).update(self.log_path.name)
        elif event.state.name == "ERROR":
            self.query_one("#title", Label).update(
                f"Unable to read log entry: {worker.error}"
            )

    def action_close(self) -> None:
        self.dismiss(None)
