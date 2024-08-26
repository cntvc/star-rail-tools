import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.notifications import Notification, Notify, SeverityLevel
from textual.widgets import ContentSwitcher, Static

from star_rail.config import settings
from star_rail.module import HSRClient
from star_rail.module.info import get_sys_info
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.tui.widgets.notification import HSRNotification, NotificationList
from star_rail.utils.logger import logger

from .screens import CreateAccountScreen
from .views import (
    AccountList,
    ConfigView,
    CurrentUID,
    GachaRecordView,
    HelpManual,
    MonthView,
    Sidebar,
    StatusBar,
)


class Navigation(Container):
    pass


class NavTab(Static):
    def on_click(self):
        self.app.query_one(MainView).current = self.id


class MainView(ContentSwitcher):
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
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+q", "app.quit", "退出", show=False),
    ]

    SCREENS = {
        "create_account_screen": CreateAccountScreen,
    }
    client: HSRClient

    def __init__(self):
        super().__init__()
        self.client = HSRClient()

    def compose(self) -> ComposeResult:
        with Container():
            with Navigation():
                yield NavTab("跃迁记录", id="gacha_record")
                yield NavTab("开拓月历", id="month")
                yield NavTab("设置", id="config")
                yield NavTab("帮助", id="help")
            with MainView(initial="gacha_record"):
                yield GachaRecordView(id="gacha_record")
                yield MonthView(id="month")
                yield ConfigView(id="config")
                yield HelpManual(id="help")
            yield AccountList(id="account_manager", classes="-hidden")
            yield Sidebar(classes="-hidden")
        yield StatusBar()

    @error_handler
    async def on_mount(self):
        logger.debug("============================================================")
        logger.debug(get_sys_info())

        await self.client.init()

        if settings.CHECK_UPDATE:
            self.check_update()

        # 在client初始化后再对显示账号数据相关组件进行刷新
        await self._refresh_user_list()
        if self.client.user:
            await self._refresh_account_data()

    async def _refresh_account_data(self):
        with self.app.batch_update():
            self.query_one(CurrentUID).uid = self.client.user.uid
            await self.query_one(MonthView).refresh_data()
            self.query_one(
                GachaRecordView
            ).analyze_result = await self.client.display_analysis_results()

    @on(events.LoginAccount)
    @error_handler
    async def handle_switch_account(self, event: events.LoginAccount):
        self.app.workers.cancel_group(self.app, "default")
        await self.client.login(event.uid)
        await self._refresh_account_data()
        self.notify(f"账号已切换为 {self.client.user.uid}")

    async def _refresh_user_list(self):
        await self.query_one(AccountList).refresh_uid_list()

    @on(events.ExitAccount)
    async def handle_exit_account(self):
        self.client.logout()
        self.app.workers.cancel_group(self.app, "default")
        with self.app.batch_update():
            self.query_one(CurrentUID).uid = ""
            self.query_one(MonthView).month_info = {}
            self.query_one(GachaRecordView).analyze_result = None

    @on(events.UpdateAccountList)
    @error_handler
    async def handle_add_account(self):
        await self._refresh_user_list()

    @work(exit_on_error=False)
    async def check_update(self):
        result, latest_version = await self.client.check_update()
        if result:
            self.notify(f"软件发现新版本: {latest_version}")

    @on(events.ReverseGachaRecord)
    async def handle_reverse_gacha_record(self):
        await self.query_one(GachaRecordView).reverse_record()

    @on(events.ShowLuckLevel)
    async def handle_show_luck_level(self):
        await self.query_one(GachaRecordView).show_luck_level()

    def action_toggle_sidebar(self):
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def toggle_account_list(self):
        account_list = self.query_one(AccountList)
        if account_list.is_hidden():
            self.set_focus(None)
            account_list.remove_class("-hidden")
        else:
            account_list.add_class("-hidden")

    def action_open_link(self, link: str) -> None:
        import webbrowser

        webbrowser.open(link)

    @on(events.TaskRunning)
    async def handle_task_running(self, event: events.TaskRunning):
        await self.query_one(StatusBar).add_task(event.worker)

    @on(events.TaskCancel)
    @on(events.TaskError)
    @on(events.TaskComplete)
    async def handle_task_done(self, event: events.TaskStatus):
        status_bar = self.query_one(StatusBar)
        await status_bar.remove_task(event.worker)

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float = Notification.timeout,
    ) -> None:
        # 通知固定显示3秒，这里不使用传入的 timeout 参数是由于调用时 widget 基类的 notify 方法会覆盖该值
        notification = Notification(message, title=title, severity=severity, timeout=3)
        self.post_message(Notify(notification))

        if self.app.screen.is_modal:
            return
        notice_list = self.query_one("Sidebar > NotificationList", NotificationList)
        notice_list.add(HSRNotification(message))
