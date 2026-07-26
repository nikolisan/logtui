from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Switch


class LabeledSwitch(Widget):
    DEFAULT_CSS = """
        LabeledSwitch {
            layout: horizontal;
            width: auto;
            height: auto;
            align: left middle;
        }
        LabeledSwitch > Label {
            width: auto;
            margin-right: 1;
            height: 100%;
            content-align: left middle;
        }
        LabeledSwitch > Switch {
            width: auto;
            
        }
        
    """

    value: reactive[bool] = reactive(False)

    def __init__(
        self,
        text: str,
        value: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.text = text
        self.value = value

    def compose(self) -> ComposeResult:
        yield Label(self.text)
        yield Switch(value=self.value)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.value = event.value

    def watch_value(self, value: bool) -> None:
        if self.is_mounted:
            self.query_one(Switch).value = value
