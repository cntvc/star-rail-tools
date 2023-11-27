from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Input

from star_rail.module import Account, HSRClient
from star_rail.tui.handler import error_handler


class UIDValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        if Account.verify_uid(value):
            return self.success()
        else:
            return self.failure("请输入正确格式的UID.")


class AccountDialog(Container):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(
                placeholder="输入UID后按Enter键以添加账户",
                id="uid",
                validate_on=["submitted"],
                validators=[UIDValidator()],
            )
            yield Button("读取Cookie", id="parse_cookie")

    @work(exclusive=True)
    @on(Button.Pressed, "#parse_cookie")
    @error_handler
    async def parse_cookie_and_login(self):
        client: HSRClient = self.app.client
        user = await client.create_account_with_cookie()
        if user:
            await client.login(user.uid)
            self.app.query_one("CurrentUID").uid = user.uid
            self.notify("Cookie解析成功")
        else:
            self.notify("未读取到有效Cookie", severity="warning")

    @work(exclusive=True)
    @on(Input.Submitted)
    @error_handler
    async def login_account(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            self.notify("请输入正确格式的UID", severity="warning")
            return
        client: HSRClient = self.app.client
        await client.login(event.value)
        self.app.query_one("CurrentUID").uid = event.value
        self.notify("账户设置成功")
