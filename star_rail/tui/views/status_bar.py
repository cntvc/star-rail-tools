from collections import OrderedDict

from rich.console import RenderableType
from textual import events as textual_events
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static
from textual.worker import Worker

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

        if client.user is None or uid != client.user.uid:
            self.post_message(hsr_events.LoginAccount(uid))
            self.post_message(hsr_events.UpdateAccountList())
            return

        if uid in self.app.query_one(AccountList).uid_list:
            self.notify("账号已登陆，请勿重复添加")
            return


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


class StatusBar(Horizontal):
    task_queue: OrderedDict[str, Worker] = OrderedDict()

    def compose(self) -> ComposeResult:
        yield AccountStatus()
        yield Horizontal(id="progress_status")
        yield Notice()

    def add_task(self, worker: Worker):
        self.task_queue[worker.name] = worker
        self._remove_progress_bar()
        self._add_progress_bar(worker)

    def remove_task(self, worker: Worker):
        if worker.name in self.task_queue:
            del self.task_queue[worker.name]

        self._remove_progress_bar()
        if len(self.task_queue) != 0:
            try:
                task_name = next(iter(self.task_queue))
            except StopIteration:
                # 防止不同事件循环的 task_queue 不同步导致的异常
                return
            self._add_progress_bar(self.task_queue[task_name])

    def _remove_progress_bar(self):
        self.query("#progress_status > TaskStatus").remove()

    def _add_progress_bar(self, worker: Worker):
        self.query("#progress_status > TaskStatus").remove()
        self.query_one("#progress_status", Horizontal).mount(TaskStatus(name=worker.name))
