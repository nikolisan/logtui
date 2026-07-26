from textual.app import ComposeResult
from textual.containers import Container, VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Label, LoadingIndicator


class LoadingModalScreen(ModalScreen[None]):
    __name__ = "LoadingModalScreen"
    DEFAULT_CSS = """
            LoadingModalScreen {
                align: center middle;
            }
            
            #dialog {
                padding: 1 2;
                width: 40%;
                height: auto;
                border: round $primary 80%;
            }
            
            #label {
                margin: 0 0 2 0;
                dock: top;
                width: 100%;
                height: auto;
                align: center middle;
            }
    """

    def __init__(self, text: str = "loading..."):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield VerticalGroup(
            Container(Label(self.text), id="label"),
            LoadingIndicator(),
            id="dialog",
        )
