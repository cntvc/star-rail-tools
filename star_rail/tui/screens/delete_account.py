from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Label

from star_rail.tui.widgets import SimpleButton

__all__ = ["DeleteAccountScreen"]


class DeleteAccountScreen(ModalScreen[bool]):
    def __init__(self, uid: str):
        self.uid = uid
        super().__init__()

    BINDINGS = [("escape", "cancel_delete_account", "cancel_delete_account")]

    def compose(self) -> ComposeResult:
        with Grid():
            yield Label(f"是否删除账户 {self.uid} 数据?", id="question")
            yield SimpleButton("确认", id="confirm")
            yield SimpleButton("取消", id="cancel")

    def on_simple_button_pressed(self, event: SimpleButton.Pressed):
        if event.button.id == "cancel":
            self.dismiss(False)
        else:
            self.dismiss(True)

    def action_cancel_delete_account(self):
        self.dismiss(False)
