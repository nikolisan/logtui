from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import DirectoryTree


class FilteredTreeview(DirectoryTree):
    ICON_FILE = "󰌠 "

    def filter_paths(self, paths: Iterable[Path]):
        return [path for path in paths if path.suffix == ".log" or path.is_dir()]


class FileBrowser(Widget):
    class FileSelected(Message):
        def __init__(self, path: Path):
            self.path = path
            super().__init__()

    class ManualLoadLog(Message):
        def __init__(self, directory: Path):
            self.directory = directory
            super().__init__()

    BINDINGS: ClassVar = [
        ("backspace", "goto_parent", "Goto parent"),
        ("l", "load_logs", "Load logs at directory"),
        ("m", "move_root", "Move root to cursor"),
    ]

    DEFAULT_CSS = """
    FileBrowser {
        border: round $accent 80%;
        margin: 2 1 1 1;
        padding: 1 0 0 0;
    }
    #treeview {
        scrollbar-size: 1 1;
        scrollbar-color: $panel 60%;
        width: 100%;
        height: 100%;
        background: transparent;
    }
    """

    root_path = var(Path.cwd())

    def compose(self) -> ComposeResult:
        self.border_title = "File Browser"
        yield FilteredTreeview(self.root_path, id="treeview")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        self.post_message(self.FileSelected(event.path))

    def action_move_root(self) -> None:
        tree = self.query_one(FilteredTreeview)
        node = tree.cursor_node
        if node and node.data:
            path = node.data.path
            if path.is_dir():
                self._root_change(path)
            elif path.is_file():
                self._root_change(path.parent)

    def action_goto_parent(self):
        self._root_change(self.root_path.parent)

    def action_load_logs(self):
        tree = self.query_one(FilteredTreeview)
        node = tree.cursor_node
        if node and node.data:
            path = node.data.path
            if path.is_dir():
                self.post_message(self.ManualLoadLog(path))

    def _root_change(self, path: Path):
        self.root_path = path
        self.query_one(FilteredTreeview).path = self.root_path

    def watch_root_path(self, path: Path) -> None:
        if self.is_mounted:
            self.query_one(FilteredTreeview).path = path
