import os

from loguru import logger
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import ContentSwitcher, Header, Static

from star_rail.config import settings
from star_rail.database import DATABASE_VERSION, DBManager
from star_rail.module import HSRClient, Updater
from star_rail.module.info import get_sys_info
from star_rail.tui.handler import error_handler

from .widgets import AccountDialog, ConfigDialog, Footer, GachaRecordDialog, MonthDialog, Sidebar


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
        ("ctrl+b", "toggle_sidebar", "关于..."),
        Binding("ctrl+q", "app.quit", "退出", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.client = HSRClient(None)
        self.updater = Updater()
        self.db_manager = DBManager()

    def compose(self) -> ComposeResult:
        yield Header()
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
        yield Footer()

    @work(exclusive=True)
    @error_handler
    async def on_mount(self):
        logger.debug("============================================================")
        logger.debug(get_sys_info())
        if not os.path.exists(self.db_manager.db_path):
            logger.debug("init database.")
            await self.db_manager.create_all()
            await self.db_manager.init_user_version()
        cur_db_version = await self.db_manager.user_version()
        logger.debug("Current db version: {}.", cur_db_version)
        if cur_db_version < DATABASE_VERSION:
            self.notify("正在升级数据库，请勿关闭软件.", severity="warning")
            await self.db_manager.upgrade_version()
            self.notify("升级完成")

        await self.client.init_default_account()

        if self.client.user:
            cur_user = self.query_one("CurrentUID")
            cur_user.uid = self.client.user.uid

        if settings.CHECK_UPDATE:
            self.check_update()

    @work(exclusive=True, exit_on_error=False)
    @error_handler
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
