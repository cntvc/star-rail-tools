from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input

from star_rail.module import Account
from star_rail.tui.widgets import SimpleButton

__all__ = ["CreateAccountScreen"]


class CreateAccountScreen(ModalScreen[str]):
    BINDINGS = [("escape", "cancel_create_account", "cancel_create_account")]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(
                placeholder="在此输入UID",
                max_length=9,
                id="uid_input",
            )
            yield SimpleButton("创建账户", id="create")
            yield SimpleButton("更新Cookie", id="parse_cookie")
            yield SimpleButton("返回", id="cancel")

    @on(SimpleButton.Pressed, "#parse_cookie")
    async def parse_cookie(self):
        self.dismiss("cookie")

    @on(Input.Submitted)
    @on(SimpleButton.Pressed, "#create")
    async def action_create_account(self):
        input_widget = self.query_one(Input)
        input_uid = input_widget.value
        if not Account.verify_uid(input_uid):
            self.notify("请输入正确格式的UID")
            return

        input_widget.clear()
        self.dismiss(input_uid)

    @on(SimpleButton.Pressed, "#cancel")
    async def action_cancel_create_account(self):
        self.dismiss("cancel")
