from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalGroup
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Input, ListItem, ListView, Static

from star_rail.module import Account, HSRClient

from .handler import error_handler

__all__ = ["AccountView"]


class DeleteAccountScreen(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel_delete", show=False)]

    def __init__(self, uid: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.uid = uid

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Static(f"是否删除账号 [bold #bf616a]{self.uid}[/] 数据?", id="question")
            yield Button("确认", id="confirm")
            yield Button("取消", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel_delete(self):
        self.dismiss(False)


class CreateAccountScreen(ModalScreen[str]):
    BINDINGS = [Binding("escape", "cancel_create", show=False)]

    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Input(placeholder="在此输入UID", id="input", max_length=9)
            yield Button("添加账号", id="create")
            yield Button("取消", id="cancel")

    @on(Input.Submitted)
    @on(Button.Pressed, "#create")
    async def handle_create_account(self, event):
        event.stop()
        input_widget = self.query_one(Input)
        input_uid = input_widget.value
        if not Account.verify_uid(input_uid):
            self.notify("请输入正确格式的UID")
            return

        input_widget.clear()
        self.dismiss(input_uid)

    @on(Button.Pressed, "#cancel")
    def action_cancel_create(self):
        self.dismiss("cancel")


class AccountList(ListView):
    uid_list: list[str] = reactive([], recompose=True)

    def compose(self) -> ComposeResult:
        for uid in self.uid_list:
            yield ListItem(Static(uid), id=f"uid_{uid}")

    async def refresh_uid_list(self):
        client: HSRClient = self.app.client
        self.uid_list = await client.get_uid_list()


class AccountView(Container):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.border_title = "账号列表"

    class Login(Message, bubble=True):
        def __init__(self, uid: str) -> None:
            super().__init__()
            self.uid = uid

    class Exit(Message, bubble=True):
        pass

    def compose(self) -> ComposeResult:
        yield AccountList()
        with VerticalGroup(id="option"):
            yield Button("添加账号", id="create")
            yield Button("切换账号", id="switch")
            yield Button("删除账号", id="delete")

    def is_hidden(self):
        return self.has_class("-hidden")

    def toggle_account_view(self):
        if self.is_hidden():
            self.remove_class("-hidden")
        else:
            self.add_class("-hidden")

    @on(Button.Pressed, "#create")
    @work(name="创建账号")
    @error_handler
    async def handle_create_account(self, event: Message):
        event.stop()
        res = await self.app.push_screen_wait(CreateAccountScreen())
        if res == "cancel":
            return

        input_uid = res

        client: HSRClient = self.app.client
        new_user = await client.create_account(input_uid)
        await self.query_one(AccountList).refresh_uid_list()

        if client.user is None or new_user.uid != client.user.uid:
            self.post_message(AccountView.Login(new_user.uid))
            return

    @on(Button.Pressed, "#switch")
    @error_handler
    async def handle_switch_account(self, event: Message):
        event.stop()

        account_list_widget = self.query_one(AccountList)
        if not account_list_widget.uid_list:
            self.notify("请先添加账号")
            return
        if account_list_widget.index is None:
            self.notify("请选择账号后操作")
            return
        client: HSRClient = self.app.client
        uid = account_list_widget.uid_list[account_list_widget.index]
        if client.user is None or uid != client.user.uid:
            self.post_message(AccountView.Login(uid))

    @work(name="删除账号")
    @on(Button.Pressed, "#delete")
    @error_handler
    async def handle_delete_account(self, event: Message):
        event.stop()

        uid_widget = self.query_one(AccountList)
        if not uid_widget.uid_list:
            self.notify("请先添加账号")
            return
        if uid_widget.index is None:
            self.notify("请选择账号后操作")
            return
        selected_uid = uid_widget.uid_list[uid_widget.index]
        opt_result = await self.app.push_screen_wait(DeleteAccountScreen(selected_uid))
        if opt_result is False:
            return

        client: HSRClient = self.app.client

        await client.delete_account(selected_uid)
        await self.query_one(AccountList).refresh_uid_list()

        if client.user and selected_uid == client.user.uid:
            self.query_one(AccountList).index = None
            self.post_message(AccountView.Exit())
