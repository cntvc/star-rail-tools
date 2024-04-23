from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import ListItem, ListView, Static
from textual.worker import Worker, WorkerState

from star_rail.module import HSRClient
from star_rail.tui import events
from star_rail.tui.handler import error_handler, required_account
from star_rail.tui.screens import DeleteAccountScreen
from star_rail.tui.widgets import SimpleButton

__all__ = ["AccountList"]


class AccountList(Container):
    BORDER_TITLE = "账号列表"
    uid_list: reactive[list[str]] = reactive([])

    def compose(self) -> ComposeResult:
        with ListView(id="uid_list"):
            for uid in self.uid_list:
                yield ListItem(Static(uid), id=f"uid_{uid}")
        with Vertical(id="buttons"):
            yield SimpleButton("切换账号", id="login")
            yield SimpleButton("更新Cookie", id="parse_cookie")
            yield SimpleButton("删除账号", id="delete")

    async def refresh_uid_list(self):
        client: HSRClient = self.app.client
        self.uid_list = await client.get_uid_list()

    async def watch_uid_list(self, new_uid_list: list[str]):
        uid_list_widget = self.query_one(ListView)
        await uid_list_widget.clear()
        uid_list_item = []
        for uid in new_uid_list:
            uid_list_item.append(ListItem(Static(uid), id=f"uid_{uid}"))
        uid_list_widget.extend(uid_list_item)

        # 默认高亮当前账号或第一个账号
        client: HSRClient = self.app.client
        if not client.user:
            return
        uid_list_widget.index = 0
        if client.user and client.user.uid in new_uid_list:
            uid_list_widget.index = new_uid_list.index(client.user.uid)

    @on(SimpleButton.Pressed, selector="#login")
    @work(group="account")
    @error_handler
    async def handle_login_account(self, event: SimpleButton.Pressed):
        event.stop()

        if not self.uid_list:
            self.notify("请先添加账号")
            return

        client: HSRClient = self.app.client
        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        if not client.user or uid != client.user.uid:
            self.post_message(events.LoginAccount(uid))

    @on(SimpleButton.Pressed, selector="#parse_cookie")
    @work(name="更新Cookie")
    @error_handler
    @required_account
    async def handle_parse_cookie(self, event: SimpleButton.Pressed):
        event.stop()

        client: HSRClient = self.app.client
        result = await client.parse_account_cookie()
        if not result:
            self.notify("未获取到有效 Cookie", severity="warning")
            return

        self.notify(f"账号{client.user.uid} Cookie 更新成功")

    @on(SimpleButton.Pressed, selector="#delete")
    @work(group="account")
    @error_handler
    async def handle_delete(self, event: SimpleButton.Pressed):
        event.stop()

        if not self.uid_list:
            self.notify("请先添加账号")
            return

        index = self.query_one(ListView).index
        uid = self.uid_list[index]
        opt = await self.app.push_screen_wait(DeleteAccountScreen(uid))
        if not opt:
            return

        client: HSRClient = self.app.client

        if client.user and uid == client.user.uid:
            self.post_message(events.ExitAccount())

        await client.delete_account(uid)
        self.post_message(events.UpdateAccountList())

    def is_hidden(self):
        return self.has_class("-hidden")

    @on(Worker.StateChanged)
    def handle_state_change(self, event: Worker.StateChanged):
        if event.worker.name != "更新Cookie":
            return

        state_to_event = {
            WorkerState.RUNNING: events.TaskRunning,
            WorkerState.SUCCESS: events.TaskComplete,
            WorkerState.ERROR: events.TaskError,
        }

        if event_type := state_to_event.get(event.state):
            self.post_message(event_type(event.worker.name))
