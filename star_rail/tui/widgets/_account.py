import traceback

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Input

from star_rail.module import Account, HSRClient
from star_rail.utils.logger import logger


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
                placeholder="输入UID后按Enter键以添加或登陆账户",
                id="uid",
                validate_on=["submitted"],
                validators=[UIDValidator()],
            )
            yield Button("读取Cookie", id="parse_cookie")

    @work(exclusive=True)
    @on(Button.Pressed, "#parse_cookie")
    async def parse_cookie_and_login(self):
        client: HSRClient = self.app.client
        try:
            user = await client.create_account_with_cookie()
            logger.debug(user)
            if user:
                await client.login(user.uid)
                self.app.query_one("CurrentUID").uid = user.uid
                self.notify("成功设置Cookie")
            else:
                self.notify("未读取到有效Cookie", severity="warning")
        except Exception as e:
            self.notify(str(e), severity="error")
            logger.debug(traceback.format_exc())
            return

    @work(exclusive=True)
    @on(Input.Submitted)
    async def login_account(self, event: Input.Submitted):
        if not event.validation_result.is_valid:
            self.notify("请输入正确格式的UID", severity="warning")
            return
        client: HSRClient = self.app.client
        try:
            await client.login(event.value)
            self.app.query_one("CurrentUID").uid = event.value
        except Exception as e:
            self.notify(str(e), severity="error")
            logger.debug(traceback.format_exc())
            return
        self.notify("账户设置成功")
