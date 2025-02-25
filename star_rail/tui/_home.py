from __future__ import annotations

import copy
import platform
import typing

from loguru import logger
from textual import work
from textual.app import ComposeResult, RenderResult, on
from textual.containers import Container, Horizontal
from textual.events import Click
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import ListItem, ListView, ProgressBar, Static

from star_rail import __version__
from star_rail.config import config
from star_rail.utils import Date

from ._account import AccountView
from ._footer import Footer
from ._import import ImportScreen
from ._record import RecordView
from .handler import error_handler, required_account

if typing.TYPE_CHECKING:
    from star_rail.module import HSRClient


class AccountNav(Static):
    uid: str = reactive("", layout=True)

    def render(self) -> RenderResult:
        return "UID: 未登陆" if not self.uid else f"UID: {self.uid}"

    def on_click(self, event: Click):
        event.stop()
        self.app.query_one(AccountView).toggle_account_view()

    def update_uid(self, uid: str):
        self.uid = uid


class RefreshNav(Static):
    def render(self) -> RenderResult:
        return "刷新"

    @work(name="更新跃迁记录")
    @error_handler
    @required_account
    async def on_click(self, event: Click):
        event.stop()
        client: HSRClient = self.app.client
        if config.USE_METADATA and client.metadata_is_latest is False:
            self.notify("请等待 metadata 更新完成")
            return

        opt = await self.app.push_screen_wait("refresh_screen")
        if opt == "cancel":
            return
        if opt == "full_update":
            cnt = await client.refresh_gacha_record(mode="full")
        else:
            cnt = await client.refresh_gacha_record(mode="incremental")
        if cnt > 0:
            if self.screen == self.app.screen:
                await self.app.query_one(RecordView).refresh_analyze_summary()
            else:
                self.screen.pending_refresh = True
        self.notify(f"跃迁记录更新完成, 共新增 {cnt} 条记录")


class ImportNav(Static):
    def render(self) -> RenderResult:
        return "导入"

    @work(name="导入数据")
    @error_handler
    @required_account
    async def on_click(self, event: Click):
        event.stop()
        cnt = await self.app.push_screen_wait(ImportScreen())
        if cnt > 0:
            await self.app.query_one(RecordView).refresh_analyze_summary()


class ExportNav(Static):
    def render(self) -> RenderResult:
        return "导出"

    @work(name="导出数据")
    @error_handler
    @required_account
    async def on_click(self, event: Click):
        event.stop()
        opt = await self.app.push_screen_wait("export_screen")
        client: HSRClient = self.app.client
        if opt == "execl":
            await client.export_to_execl()
        elif opt == "srgf":
            await client.export_to_srgf()
        elif opt == "uigf":
            await client.export_to_uigf()
        else:
            pass
        self.notify("导出完成")


class HelpNav(Static):
    def render(self) -> RenderResult:
        return "帮助"

    def on_click(self, event: Click):
        event.stop()
        self.app.switch_mode("help")


class TaskList(Container):
    task_list: list = reactive([], recompose=True)

    def compose(self) -> ComposeResult:
        with ListView() as listview:
            listview.border_title = "任务列表"
            for task_name in self.task_list:
                yield ListItem(TaskBar(name=task_name))

    @property
    def is_hidden(self):
        return self.has_class("-hidden")

    def toggle_task_list(self):
        if self.is_hidden:
            self.remove_class("-hidden")
        else:
            self.add_class("-hidden")


class TaskBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static(self.name, id="task_name")
        yield ProgressBar(show_percentage=False, show_eta=False)

    def on_click(self, event: Click):
        event.stop()
        self.app.query_one(TaskList).toggle_task_list()


class HomeScreen(Screen):
    FOOTER_KEY = [AccountNav, RefreshNav, ImportNav, ExportNav, HelpNav]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client: HSRClient = self.app.client
        self.pending_refresh = False

    def compose(self) -> ComposeResult:
        with Container(id="main_content"):
            yield AccountView(classes="-hidden")
            yield RecordView()
            yield TaskList(classes="-hidden")
        yield Footer()

    async def on_mount(self) -> None:
        logger.debug(
            "Starting Star Rail Tools...\n"
            f"Software version:{__version__}\n"
            f"System time:{Date.now().strftime(Date.Format.YYYY_MM_DD_HHMMSS)}\n"
            f"System version:{platform.platform()}\n"
            f"Config: {config.model_dump()}"
        )
        await self.client.init()

        await self.query_one("AccountView > AccountList").refresh_uid_list()
        if self.client.user:
            await self._init_view()

        self.set_interval(1 / 4, self.update_worker_list)

    def action_toggle_account_view(self) -> None:
        self.query_one(AccountView).toggle_account_view()

    @on(AccountView.Login)
    async def handle_login_account(self, event: AccountView.Login):
        login_uid = event.uid
        self.app.workers.cancel_group(self.app, "default")
        await self.client.login(login_uid)
        await self._refresh_view()
        self.notify(f"账号已切换为 {self.client.user.uid}")

    @on(AccountView.Exit)
    async def handle_exit_account(self):
        self.app.workers.cancel_group(self.app, "default")
        self._reset_view()
        await self.client.logout()

    async def _refresh_view(self) -> None:
        with self.app.batch_update():
            self.query_one("Footer > AccountNav", AccountNav).update_uid(self.client.user.uid)
            await self.query_one(RecordView).refresh_analyze_summary()

    def _reset_view(self):
        with self.app.batch_update():
            self.query_one("Footer > AccountNav", AccountNav).update_uid("")
            self.query_one(RecordView).reset_analyze_summary()

    async def _init_view(self):
        with self.app.batch_update():
            self.query_one("Footer > AccountNav", AccountNav).update_uid(self.client.user.uid)
            await self.query_one(RecordView).load_analyze_summary()

    def update_worker_list(self):
        workers = list(copy.copy(self.app.workers._workers))
        if not workers:
            if res := self.query(TaskBar):
                res.remove()
            task_list_widget = self.query_one(TaskList)
            if not task_list_widget.is_hidden:
                task_list_widget.toggle_task_list()
            return

        task_list = [work.name for work in workers]
        self.query_one(TaskList).task_list = task_list
        if res := self.query(TaskBar):
            task_bar = res.first()
            if task_bar.name == task_list[0]:
                return
            task_bar.remove()
            self.query_one(Footer).mount(TaskBar(name=task_list[0]))
        else:
            self.query_one(Footer).mount(TaskBar(name=task_list[0]))

    async def on_screen_resume(self):
        if self.pending_refresh is True:
            await self.query_one(RecordView).refresh_analyze_summary()
            self.pending_refresh = False
