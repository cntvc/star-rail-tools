from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Select, Static, Switch

from star_rail.config import settings


class ConfigDialog(Container):
    def compose(self) -> ComposeResult:
        yield ConfigSwitchItem("CHECK_UPDATE", "自动检测更新", settings.CHECK_UPDATE)
        yield ConfigSwitchItem("DISPLAY_STARTER_WARP", "显示新手池数据", settings.DISPLAY_STARTER_WARP)


class ConfigSwitchItem(Horizontal):
    def __init__(self, id: str, desc: str, status: bool, **kwargs) -> None:
        super().__init__(id=id, **kwargs)
        self.desc = desc
        self.status = status

    def compose(self) -> ComposeResult:
        yield Static(self.desc)
        yield Switch(value=self.status)

    @on(Switch.Changed)
    def update_settings(self, event: Select.Changed):
        settings.update_config({self.id: event.value})
        settings.save_config()
