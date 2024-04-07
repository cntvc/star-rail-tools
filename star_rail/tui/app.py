import os

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.notifications import Notification, Notify, SeverityLevel
from textual.widgets import ContentSwitcher, Static

from star_rail.config import settings
from star_rail.module import HSRClient, Updater
from star_rail.module.info import get_sys_info
from star_rail.tui import events
from star_rail.tui.handler import error_handler
from star_rail.tui.widgets.notification import HSRNotification
from star_rail.utils.logger import logger

from .pages import (
    AccountManagerDialog,
    ConfigDialog,
    CurrentUID,
    GachaRecordDialog,
    HelpMenual,
    MonthDialog,
    Sidebar,
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
        ("ctrl+b", "toggle_sidebar", "Sidebar"),
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
        self.task_queue = set()

    def compose(self) -> ComposeResult:
        with Container():
            with Navigation():
                yield NavTab("账号管理", id="account_manager")
                yield NavTab("跃迁记录", id="gacha_record")
                yield NavTab("开拓月历", id="month")
                yield NavTab("设置", id="config")
                yield NavTab("帮助", id="help")
            with MainDialog(initial="account_manager"):
                yield AccountManagerDialog(id="account_manager")
                yield GachaRecordDialog(id="gacha_record")
                yield MonthDialog(id="month")
                yield ConfigDialog(id="config")
                yield HelpMenual(id="help")
            yield Sidebar(classes="-hidden")

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
            await self.query_one(MonthDialog).refresh_data()
            self.query_one(GachaRecordDialog).analyze_result = (
                await self.client.view_analysis_results()
            )

    @on(events.LoginAccount)
    @error_handler
    async def handle_switch_account(self):
        self.app.workers.cancel_all()
        await self._refresh_account_data()
        self.notify("账号切换成功.")

    async def _refresh_user_list(self):
        self.query_one(AccountManagerDialog).uid_list = await self.client.get_uid_list()

    @on(events.ExitAccount)
    async def handle_exit_account(self):
        self.app.workers.cancel_all()
        with self.app.batch_update():
            self.query_one(CurrentUID).uid = ""
            self.query_one(MonthDialog).month_info_list = []
            self.query_one(GachaRecordDialog).analyze_result = None

    @on(events.UpdateAccountList)
    @error_handler
    async def handle_add_account(self):
        await self._refresh_user_list()

    @work(exit_on_error=False)
    async def check_update(self):
        result = await self.updater.check_update()
        if result:
            self.notify("软件发现新版本.")

    @on(events.ReverseGachaRecord)
    async def handle_reverse_gacha_record(self):
        await self.query_one(GachaRecordDialog).reverse_record()

    @on(events.ShowLuckLevel)
    async def handle_show_luck_level(self):
        await self.query_one(GachaRecordDialog).show_luck_level()

    def action_toggle_sidebar(self) -> None:
        self._toggle_sidebar()

    def _toggle_sidebar(self):
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_open_link(self, link: str) -> None:
        import webbrowser

        webbrowser.open(link)

    @on(events.TaskRunning)
    def handle_task_running(self, event: events.TaskRunning):
        self.task_queue.add(event.name)
        self.query_one(StatusBar).add_task_bar(name=event.name)

    @on(events.TaskCancel)
    @on(events.TaskError)
    @on(events.TaskComplete)
    def handle_task_complete(self, event: events.TaskComplete):
        self.task_queue.remove(event.name)

        if len(self.task_queue) == 0:
            self.query_one(StatusBar).remove_task_bar()
        else:
            name = next(iter(self.app.workers))
            self.query_one(StatusBar).update_task_bar(name=name)

    def notify(
        self,
        message: str,
        *,
        title: str = "",
        severity: SeverityLevel = "information",
        timeout: float = 3,
    ) -> None:

        notification = Notification(message, title, severity, timeout)
        self.post_message(Notify(notification))
        # 模态对话框发出通知，但是通知栏在下层屏幕，无法捕获消息
        # 因为对话框的通知一般是校验提示信息，这里不进行特殊处理，不加入通知栏
        if notice_list := self.query("Sidebar > NotificationList"):
            notice_list.first().add(HSRNotification(message))
