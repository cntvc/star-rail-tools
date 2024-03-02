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
            yield SimpleButton("切换账号", id="switch")
            yield SimpleButton("删除账号", id="delete")
        with ListView():
            for uid in self.uid_list:
                yield ListItem(Label(uid), id=f"uid_{uid}")

    async def watch_uid_list(self, uid_list: list[str]):
        uid_list_widget = self.query_one(ListView)
        await uid_list_widget.clear()
        for uid in uid_list:
            await uid_list_widget.append(ListItem(Label(uid), id=f"uid_{uid}"))

    @on(SimpleButton.Pressed, "#add")
    @work()
    @error_handler
    async def add_account(self):
        opt = await self.app.push_screen_wait("create_account_screen")

        client: HSRClient = self.app.client
        if opt == "cancel":
            return
        elif opt == "cookie":
            user = await client.parse_account_cookie()
            if not user:
                self.notify("未读取到有效Cookie", severity="warning")
            else:
                self.notify(f"已更新账号 {user.uid} 的Cookie")
                # Cookie 对应的账号是当前已登陆账号时，直接替换以更新Cookie
                if user.uid == client.user.uid:
                    client.user = user
        else:
            await client.create_account_by_uid(opt)
        self.post_message(events.ChangeAccountList())

    @on(SimpleButton.Pressed, "#switch")
    @work(group="add_account")
    @error_handler
    async def switch_account(self):
        if not self.uid_list:
            self.notify("请先添加账号")
            return
        client: HSRClient = self.app.client
        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        if not client.user or uid != client.user.uid:
            self.app.workers.cancel_group(self.app, group="default")
            await self._login_account(uid)

    async def _login_account(self, uid: str):
        client: HSRClient = self.app.client
        await client.login(uid)
        self.post_message(events.SwitchAccount())
        self.notify(f"切换为账号{uid}")

    @on(SimpleButton.Pressed, "#delete")
    @work(group="delete_account")
    @error_handler
    async def delete_account(self):
        if not self.uid_list:
            self.notify("请先添加账号")
            return

        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        opt = await self.app.push_screen_wait(DeleteAccountScreen(uid))
        if not opt:
            return

        client: HSRClient = self.app.client
        if client.user and uid != client.user.uid:
            await client.delete_account(uid)
            self.post_message(events.ChangeAccountList())
        else:
            # 删除的是当前登陆的账户
            self.app.workers.cancel_group(self.app, "default")
            await client.delete_account(uid)
            client.user = None
            self.post_message(events.ExitAccount())
            self.post_message(events.ChangeAccountList())
