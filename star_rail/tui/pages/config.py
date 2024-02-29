from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Switch

from star_rail.config import settings


class ConfigDialog(Container):
    def compose(self) -> ComposeResult:
        yield ConfigSwitchItem("CHECK_UPDATE", "自动检测更新", settings.CHECK_UPDATE)


class ConfigSwitchItem(Horizontal):
    def __init__(self, switch_id: str, desc: str, status: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.switch_id = switch_id
        self.desc = desc
        self.status = status

    def compose(self) -> ComposeResult:
        yield Static(self.desc)
        yield Switch(value=self.status, id=self.switch_id)

    @on(Switch.Changed, "#CHECK_UPDATE")
    def _change_check_update(self, event: Switch.Changed):
        settings.CHECK_UPDATE = event.value
        settings.save_config()
