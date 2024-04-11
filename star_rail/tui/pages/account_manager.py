from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView

from star_rail.module import HSRClient
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.tui.screens import DeleteAccountScreen
from star_rail.tui.widgets import SimpleButton

__all__ = ["AccountManagerDialog"]


class AccountManagerDialog(Container):
    uid_list: reactive[list[str]] = reactive([])

    def compose(self) -> ComposeResult:
        with Vertical():
            yield SimpleButton("添加账号", id="add")
            yield SimpleButton("切换账号", id="login")
            yield SimpleButton("删除账号", id="delete")
        with ListView():
            for uid in self.uid_list:
                yield ListItem(Label(uid), id=f"uid_{uid}")

    async def watch_uid_list(self, uid_list: list[str]):
        uid_list_widget = self.query_one(ListView)
        await uid_list_widget.clear()
        uid_list_item = []
        for uid in uid_list:
            uid_list_item.append(ListItem(Label(uid), id=f"uid_{uid}"))
        uid_list_widget.extend(uid_list_item)
        if uid_list:
            uid_list_widget.index = 0

    @on(SimpleButton.Pressed, "#add")
    @work()
    @error_handler
    async def handle_add_account(self):
        opt = await self.app.push_screen_wait("create_account_screen")

        if opt == "cancel":
            return

        client: HSRClient = self.app.client

        if opt == "cookie":
            uid = await client.parse_account_cookie()
            if not uid:
                self.notify("未读取到有效Cookie", severity="warning")
                return
            self.notify(f"账号{uid} Cookie已更新")
        else:
            uid = await client.create_account_by_uid(opt)

        # 创建的账号是当前已登陆账号时，更新数据（Cookie）
        if client.user and uid == client.user.uid:
            await client.user.load_profile()
            return
        else:
            await self._login_account(uid)

        if uid not in self.uid_list:
            self.post_message(events.UpdateAccountList())

    @on(SimpleButton.Pressed, "#login")
    @work()
    @error_handler
    async def handle_login_account(self):
        if not self.uid_list:
            self.notify("请先添加账号")
            return
        client: HSRClient = self.app.client
        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        if not client.user or uid != client.user.uid:
            await self._login_account(uid)

    async def _login_account(self, uid: str):
        client: HSRClient = self.app.client
        await client.login(uid)
        self.post_message(events.LoginAccount())

    @on(SimpleButton.Pressed, "#delete")
    @work()
    @error_handler
    async def handle_delete_account(self):
        if not self.uid_list:
            self.notify("请先添加账号")
            return

        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        deletion_confirmed = await self.app.push_screen_wait(DeleteAccountScreen(uid))
        if not deletion_confirmed:
            return

        client: HSRClient = self.app.client
        if client.user and uid != client.user.uid:
            await client.delete_account(uid)
            self.post_message(events.UpdateAccountList())
        else:
            # 删除的是当前登陆的账号
            await client.delete_account(uid)
            client.user = None
            self.post_message(events.ExitAccount())
            self.post_message(events.UpdateAccountList())
