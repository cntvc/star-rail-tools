from rich.console import RenderableType
from textual import events as textual_events
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static

from star_rail.module import HSRClient
from star_rail.tui import events as hsr_events

from .account_list import AccountList

__all__ = ["StatusBar", "CurrentUID"]


class CurrentUID(Static):
    uid = reactive("", layout=True)

    def render(self) -> RenderableType:
        return "UID: 未登陆" if not self.uid else f"UID: {self.uid}"

    async def on_click(self, event: textual_events.Click) -> None:
        event.stop()
        self.app.toggle_account_list()


class AddAccount(Static):
    def render(self) -> RenderableType:
        return "+"

    @work(group="account")
    async def on_click(self, event: textual_events.Click) -> None:
        event.stop()
        result = await self.app.push_screen_wait("create_account_screen")

        if result == "cancel":
            return

        client: HSRClient = self.app.client
        uid = await client.create_account_by_uid(result)

        if uid in self.app.query_one(AccountList).uid_list:
            self.notify("账号已存在，请勿重复添加")
            return

        # 创建账号不是已登陆账号时，自动登录新账号
        if client.user is None or uid != client.user.uid:
            self.post_message(hsr_events.LoginAccount(uid))

        self.post_message(hsr_events.UpdateAccountList())


class AccountStatus(Horizontal):
    def compose(self) -> ComposeResult:
        yield CurrentUID()
        yield AddAccount()


class Notice(Static):

    def render(self) -> RenderableType:
        return "通知"

    def on_click(self, event: textual_events.Click) -> None:
        event.stop()
        self.app.action_toggle_sidebar()


class TaskStatus(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static(self.name, id="task_name")
        yield ProgressBar(show_percentage=False, show_eta=False)

    def update(self, name: str):
        self.name = name
        self.query_one("#task_name", Static).update(name)


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield AccountStatus()
        yield Horizontal(id="progress_status")
        yield Notice()

    def add_progress_bar(self, **kwargs):
        self.query_one("#progress_status", Horizontal).mount(TaskStatus(**kwargs))

    def remove_progress_bar(self):
        self.query_one("#progress_status > TaskStatus", TaskStatus).remove()

    def update_progress_bar(self, name: str):
        task_bar = self.query_one("#progress_status", Horizontal)
        if task_status := task_bar.query(TaskStatus):
            task_status.first().update(name)
