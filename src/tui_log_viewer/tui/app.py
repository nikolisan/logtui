from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.reactive import var
from textual.widgets import Footer, Header
from textual.worker import Worker

from tui_log_viewer.cli.parser import LogParser
from tui_log_viewer.tui.components import FileBrowser, LogViewerComponent
from tui_log_viewer.tui.Screens import DirectoryPickModalScreen, LoadingModalScreen


class LogViewerApp(App[None]):
    BINDINGS: ClassVar = [
        ("f1", "change_directory", "Change directory"),
        ("q", "quit", "Quit"),
        ("b", "toggle_sidebar", "Toggle file browser"),
    ]

    CSS_PATH = "style.tcss"
    TITLE = "LogViewer"
    SUB_TITLE = "Simple python based log viewer"

    directory: var[Path] = var(Path.home() / ".logtui")

    show_sidebar: var[bool] = var(True)

    file_path: var[Path] = var(Path(""), init=False)
    loading_logs: var[bool] = var(False)
    log_parser: var[LogParser | None] = var(None, init=False)

    _logs_loaded: var[bool] = var(False)
    _force_load: var[bool] = var(False)
    _auto_load_logs: var[bool] = var(False)

    def __init__(self):
        super().__init__()
        self.screens = {"directory_pick": DirectoryPickModalScreen}
        self._parser_worker: Worker[LogParser] | None = None

    def compose(self) -> ComposeResult:
        yield FileBrowser(id="file-browser")
        yield LogViewerComponent()
        yield Header()
        yield Footer(show_command_palette=False)

    def on_mount(self):
        self.query_one(FileBrowser).data_bind(root_path=LogViewerApp.directory)
        self.query_one(LogViewerComponent).data_bind(
            _file_path=LogViewerApp.file_path, _parser=LogViewerApp.log_parser
        )

    def request_log_load(self, directory: Path):
        directory = directory.resolve()

        self._auto_load_logs = True
        self._logs_loaded = False

        if directory == self.directory.resolve():
            self._start_parser_load(directory)
        else:
            self.directory = directory

    def _start_parser_load(self, directory: Path) -> None:
        self.loading_logs = True
        self.notify(f"Loading logs from {directory}", timeout=1)
        self._parser_worker = self.load_parser(directory)

    # --- Actions --- #

    def action_toggle_sidebar(self):
        self.show_sidebar = not self.show_sidebar

    def action_change_directory(self):
        def _notify(msg: Path | None) -> None:
            if msg:
                self.notify(str(msg))
                self.directory = msg

        self.push_screen(DirectoryPickModalScreen(path=str(Path.cwd())), _notify)

    #  --- Watchers --- #

    def watch_loading_logs(self, loading: bool) -> None:
        if loading:
            if not isinstance(self.screen, LoadingModalScreen):
                self.push_screen(
                    LoadingModalScreen(f"Loading logs from {self.directory}")
                )
        else:
            if isinstance(self.screen, LoadingModalScreen):
                self.pop_screen()

    def watch_show_sidebar(self):
        _class = "hidden" if not self.show_sidebar else ""
        self.query_one("#file-browser", FileBrowser).set_classes(_class)

    def watch_directory(self, directory: Path) -> None:
        if self._auto_load_logs and not self._logs_loaded:
            self._start_parser_load(directory)

    # --- Event handlers --- #

    def on_file_browser_file_selected(self, event: FileBrowser.FileSelected) -> None:
        self.file_path = event.path
        directory = event.path.parent.resolve()

        if (
            self.log_parser is not None
            and self._logs_loaded
            and self.directory.resolve() == directory
        ):
            # select the file without re-loading the parser
            return

        self.request_log_load(event.path.parent)

    def on_file_browser_manual_load_log(self, event: FileBrowser.ManualLoadLog) -> None:
        self.request_log_load(event.directory)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker != self._parser_worker:  # pyright: ignore[reportUnknownMemberType]
            return

        if event.state.name == "SUCCESS":
            self.log_parser = event.worker.result  # pyright: ignore[reportUnknownMemberType]
            self.notify("Log files loaded", timeout=2)
            self._auto_load_logs = False
            self.loading_logs = False
            self._logs_loaded = True

        elif event.state.name == "ERROR":
            self.log_parser = None
            self.loading_logs = False
            self._auto_load_logs = False
            self.notify(f"Failed to load logs {event.worker.error}")  # pyright: ignore[reportUnknownMemberType]
            self.log(f"Failed to load logs {event.worker.error}")  # pyright: ignore[reportUnknownMemberType]
            self._logs_loaded = False

    @work(thread=True, exclusive=True, exit_on_error=False)
    def load_parser(self, directory: Path) -> LogParser:
        return LogParser(directory, self._auto_load_logs)


def run():
    app = LogViewerApp()
    app.run()


if __name__ == "__main__":
    run()
