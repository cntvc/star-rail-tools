import os

from textual import work
from textual.app import App

from star_rail.config import config
from star_rail.module import HSRClient

from ._export import ExportScreen
from ._help import HelpScreen
from ._home import HomeScreen
from ._refresh import RefreshScreen
from .handler import error_handler


class HSRApp(App):
    client: HSRClient
    CSS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.tcss")
    SCREENS = {
        "export_screen": ExportScreen,
        "refresh_screen": RefreshScreen,
    }
    MODES = {
        "help": HelpScreen,
        "home": HomeScreen,
    }
    DEFAULT_MODE = "home"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = HSRClient()

    def on_mount(self):
        if config.CHECK_UPDATE:
            self.check_update()

        if config.USE_METADATA:
            self.check_and_update_metadata()

    @work(name="检测软件更新", exit_on_error=False, group="app")
    @error_handler
    async def check_update(self):
        if new_version := await self.client.check_app_update():
            self.notify(f"发现新版本: {new_version}")

    @work(name="更新metadata", exit_on_error=False, group="app")
    @error_handler
    async def check_and_update_metadata(self):
        await self.client.check_and_update_metadata()

    def action_open_link(self, link: str) -> None:
        import webbrowser

        webbrowser.open(link)
