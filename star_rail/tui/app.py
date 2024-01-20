import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import ContentSwitcher, Static

from star_rail.config import settings
from star_rail.module import HSRClient, Updater
from star_rail.module.info import get_sys_info
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.utils.logger import logger

from .pages import (
    AccountDialog,
    ConfigDialog,
    CurrentUID,
    GachaRecordDialog,
    MonthDialog,
    Sidebar,
    StatusBar,
)


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

"""调用逻辑

主界面消费 loginAccount，使 status_bar 更新uid，跃迁记录查询本地，开拓月历查询本地
"""


class HSRApp(App):
    TITLE = "StarRailTools"
    CSS_PATH = tcss_list
    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "关于..."),
        ("ctrl+p", "command_palette", "命令行"),
        Binding("ctrl+q", "app.quit", "退出", show=False),
    ]

    client: HSRClient

    def __init__(self):
        super().__init__()
        self.client = HSRClient(None)
        self.updater = Updater()

    def compose(self) -> ComposeResult:
        with Container():
            yield Sidebar(classes="-hidden")
            with Navigation():
                yield NavTab("账户管理", id="account_manager")
                yield NavTab("跃迁记录", id="gacha_record")
                yield NavTab("开拓月历", id="month")
                yield NavTab("设置", id="config")
            with MainDialog(initial="account_manager"):
                yield AccountDialog(id="account_manager")
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

        if not self.client.user:
            return

        await self.reset_account_data()

    async def reset_account_data(self):
        self.query_one(CurrentUID).uid = self.client.user.uid
        self.query_one(MonthDialog).month_info_list = await self.client.get_month_info_in_range()
        self.query_one(GachaRecordDialog).analyze_result = await self.client.view_analysis_results()

    @on(events.LoginAccount)
    @error_handler
    async def login_account(self):
        await self.reset_account_data()

    @work(exclusive=True, exit_on_error=False)
    async def check_update(self):
        result = await self.updater.check_update()
        if result:
            self.notify("软件发现新版本.")

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_open_link(self, link: str) -> None:
        self.app.bell()
        import webbrowser

        webbrowser.open(link)
