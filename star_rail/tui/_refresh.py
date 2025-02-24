from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.screen import ModalScreen
from textual.widgets import Button


class RefreshScreen(ModalScreen[str]):
    BINDINGS = [("escape", "handle_cancel", "cancel_refresh")]

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Button("增量刷新", id="incremental_update")
            yield Button("全量刷新", id="full_update")
            yield Button("取消", id="cancel")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id)

    def action_handle_cancel(self):
        self.dismiss("cancel")
