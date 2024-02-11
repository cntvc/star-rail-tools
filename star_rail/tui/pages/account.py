from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Input

from star_rail.module import Account, HSRClient
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.tui.widgets import SimpleButton


class AccountDialog(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(
                placeholder="在此输入UID",
                id="uid",
            )
            yield SimpleButton("登陆", id="login")
            yield SimpleButton("读取Cookie", id="parse_cookie")

    @work()
    @on(SimpleButton.Pressed, "#parse_cookie")
    @error_handler
    async def parse_cookie_and_login(self):
        client: HSRClient = self.app.client
        user = await client.create_account_with_cookie()
        if user:
            await client.login(user.uid)
            self.notify("Cookie解析成功")
            self.post_message(events.SwitchUser())
        else:
            self.notify("未读取到有效Cookie", severity="warning")

    @work()
    @on(SimpleButton.Pressed, "#login")
    @error_handler
    async def login_account_by_button(self):
        input = self.query_one(Input)
        if not await self.login_account(input.value):
            return

        input.value = ""

    @work()
    @on(Input.Submitted)
    @error_handler
    async def login_account_by_key(self, event: Input.Submitted):
        if not await self.login_account(event.value):
            return

        self.query_one(Input).value = ""

    async def login_account(self, uid: str):
        if not Account.verify_uid(uid):
            self.notify("请输入正确格式的UID", severity="warning")
            return False

        client: HSRClient = self.app.client
        await client.login(uid)

        self.post_message(events.SwitchUser())
        self.notify("账户设置成功")
        return True
