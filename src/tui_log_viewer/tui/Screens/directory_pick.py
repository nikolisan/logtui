from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, VerticalGroup
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label


class DirectoryPickModalScreen(ModalScreen[Path | None]):
    __name__ = "DirectoryPickScreen"
    DEFAULT_CSS = """
            DirectoryPickScreen {
                align: center middle;
            }
            #dialog {
                padding: 1 2;
                width: 70%;
                height: auto;
                border: round $primary 80%;
            }
            #label {
                width: 100%;
                height: auto;
                align: center middle;
                margin: 0 0 2 0;
            }
    """

    path: reactive[str] = reactive("")

    BINDINGS = [  # noqa: RUF012
        ("escape", "dismiss_screen", "Dismiss")
    ]

    def __init__(self, path: str | Path) -> None:
        super().__init__()
        self.set_reactive(DirectoryPickModalScreen.path, str(path))

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            Container(Label("Enter new root directory"), id="label"),
            Input(value=self.path, placeholder="Enter new root directory", id="input"),
            id="dialog",
        )
        yield Footer(show_command_palette=False, compact=True)

    def on_mount(self) -> None:
        self.query_one("#input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.path = event.value

    def action_dismiss_screen(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        out = Path(event.value).expanduser().resolve()
        if not out.is_dir():
            self.notify(f"Directory does not exist: {out}", severity="error")
            return
        self.dismiss(out)
