from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView

from star_rail.module import HSRClient
from star_rail.tui import events
from star_rail.tui.widgets import SimpleButton

__all__ = ["AccountManagerDialog"]


class AccountManagerDialog(Container):
    uid_list: reactive[list[str]] = reactive([])

    def compose(self) -> ComposeResult:
        with Vertical():
            yield SimpleButton("添加账号", id="add")
            yield SimpleButton("切换账号", id="switch")
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
    async def add_account(self):
        uid = await self.app.push_screen_wait("create_account_screen")
        client: HSRClient = self.app.client
        if not uid:
            return
        await client.login(uid)
        self.post_message(events.SwitchAccount())
        self.notify(f"切换为账号{uid}", timeout=1)
        self.uid_list = await client.get_uid_list()

    @on(SimpleButton.Pressed, "#switch")
    @work()
    async def switch_account(self):
        if not self.uid_list:
            self.notify("请先添加账号")
            return
        client: HSRClient = self.app.client
        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        if not client.user or uid != client.user.uid:
            await client.login(uid)
            self.notify(f"切换为账号{uid}", timeout=1)
            self.post_message(events.SwitchAccount())
