import os
import platform

from loguru import logger
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container

from star_rail import __version__
from star_rail.config import config
from star_rail.module import HSRClient
from star_rail.utils import Date

from .widgets import AccountView, ExportScreen, Footer, HelpScreen, RecordView, RefreshScreen


class HSRApp(App):
    client: HSRClient
    CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.tcss")
    SCREENS = {
        "export_screen": ExportScreen,
        "refresh_screen": RefreshScreen,
        "help_screen": HelpScreen,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = HSRClient()

    def compose(self) -> ComposeResult:
        with Container(id="main_content"):
            yield AccountView(classes="-hidden")
            yield RecordView()
        yield Footer()

    async def on_mount(self) -> None:
        logger.debug(
            "Starting Star Rail Tools...\n"
            f"Software version:{__version__}\n"
            f"System time:{Date.now().strftime(Date.Format.YYYY_MM_DD_HHMMSS)}\n"
            f"System version:{ platform.platform()}\n"
            f"Config: {config.model_dump()}"
        )
        await self.client.init()

        if config.CHECK_UPDATE:
            self.check_update()

        if config.USE_METADATA:
            self.check_and_update_metadata()

        if self.client.user:
            self._init_view()

        # TODO 定时任务，获取 worker list 并显示在 Footer

    @work(name="检测软件更新", exit_on_error=False, group="app")
    async def check_update(self):
        if new_version := await self.client.check_app_update():
            self.notify(f"发现新版本: {new_version}")

    @work(name="更新元数据", exit_on_error=False, group="app")
    async def check_and_update_metadata(self):
        await self.client.check_and_update_metadata()

    @on(AccountView.Login)
    async def handle_login_account(self, event: AccountView.Login):
        login_uid = event.uid
        self.app.workers.cancel_group(self.app, "default")
        await self.client.login(login_uid)
        await self._refresh_view()
        self.notify(f"账号已切换为 {self.client.user.uid}")

    @on(AccountView.Exit)
    def handle_exit_account(self):
        self.app.workers.cancel_group(self.app, "default")
        self._reset_view()

    async def _refresh_view(self) -> None:
        with self.app.batch_update():
            self.query_one("Footer > UserNav").update_uid(self.client.user.uid)
            await self.query_one(RecordView).refresh_analyze_summary()

    def _reset_view(self):
        with self.app.batch_update():
            self.query_one("Footer > UserNav").update_uid("")
            self.query_one(RecordView).reset_analyze_summary()

    def _init_view(self):
        with self.app.batch_update():
            self.query_one("Footer > UserNav").update_uid(self.client.user.uid)
            self.query_one(RecordView).load_analyze_summary()
