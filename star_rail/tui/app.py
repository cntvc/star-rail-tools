import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import ContentSwitcher, Static, TabbedContent

from star_rail.config import settings
from star_rail.module import HSRClient, Updater
from star_rail.module.info import get_sys_info
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.tui.pages.record import RecordDetail
from star_rail.utils.logger import logger

from .pages import (
    AccountManagerDialog,
    ConfigDialog,
    CurrentUID,
    GachaRecordDialog,
    MonthDialog,
    StatusBar,
)
from .screens import CreateAccountScreen


class Navigation(Container):
    pass


class NavTab(Static):
    def on_click(self):
        self.app.query_one(MainDialog).current = self.id


class MainDialog(ContentSwitcher):
    pass


def get_tcss_list():
    # 使用相对路径访问
    tcss_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tcss")
    return [os.path.join(tcss_dir, name) for name in os.listdir(tcss_dir) if name.endswith(".tcss")]


tcss_list = get_tcss_list()


class HSRApp(App):
    TITLE = "StarRailTools"
    CSS_PATH = tcss_list
    BINDINGS = [
        ("ctrl+p", "command_palette", "命令行"),
        Binding("ctrl+q", "app.quit", "退出", show=False),
    ]

    SCREENS = {
        "create_account_screen": CreateAccountScreen(),
    }
    client: HSRClient

    def __init__(self):
        super().__init__()
        self.client = HSRClient(None)
        self.updater = Updater()

    def compose(self) -> ComposeResult:
        with Container():
            with Navigation():
                yield NavTab("账号管理", id="account_manager")
                yield NavTab("跃迁记录", id="gacha_record")
                yield NavTab("开拓月历", id="month")
                yield NavTab("设置", id="config")
            with MainDialog(initial="account_manager"):
                yield AccountManagerDialog(id="account_manager")
                yield GachaRecordDialog(id="gacha_record")
                yield MonthDialog(id="month")
                yield ConfigDialog(id="config")
        yield StatusBar()

    @error_handler
    async def on_mount(self):
        logger.debug("============================================================")
        logger.debug(get_sys_info())

        await self.client.start()

        if settings.CHECK_UPDATE:
            self.check_update()

        # 在client初始化后再对显示账号数据相关组件进行刷新
        await self._refresh_user_list()
        if self.client.user:
            await self._refresh_account_data()

    async def _refresh_account_data(self):
        with self.app.batch_update():
            self.query_one(CurrentUID).uid = self.client.user.uid
            self.query_one(
                MonthDialog
            ).month_info_list = await self.client.get_month_info_in_range()
            self.query_one(
                GachaRecordDialog
            ).analyze_result = await self.client.view_analysis_results()

    @on(events.SwitchAccount)
    @error_handler
    async def login_account(self):
        await self._refresh_account_data()

    async def _refresh_user_list(self):
        self.query_one(AccountManagerDialog).uid_list = await self.client.get_uid_list()

    @on(events.ExitAccount)
    async def exit_account(self):
        with self.app.batch_update():
            self.query_one(CurrentUID).uid = ""
            self.query_one(MonthDialog).month_info_list = []
            self.query_one(GachaRecordDialog).analyze_result = None

    @on(events.ChangeAccountList)
    @work()
    @error_handler
    async def add_account(self):
        await self._refresh_user_list()

    @on(events.ChangeStarterWarp)
    def change_starter_warp(self, event: events.ChangeStarterWarp):
        record_detail = self.query(RecordDetail)
        if record_detail:
            tab_c = record_detail.first().query_one(TabbedContent)
            if event.value:
                tab_c.show_tab("STARTER_WARP")
            else:
                tab_c.hide_tab("STARTER_WARP")

    @work(exit_on_error=False)
    async def check_update(self):
        result = await self.updater.check_update()
        if result:
            self.notify("软件发现新版本.")
