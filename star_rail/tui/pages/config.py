from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Switch

from star_rail.config import settings
from star_rail.tui.events import ReverseGachaRecord


class ConfigDialog(Container):
    def compose(self) -> ComposeResult:
        yield ConfigSwitchItem(
            switch_id="CHECK_UPDATE", desc="自动检测更新", status=settings.CHECK_UPDATE
        )
        yield ConfigSwitchItem(
            switch_id="REVERSE_ORDER", desc="倒序显示跃迁记录", status=settings.REVERSE_ORDER
        )


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

    @on(Switch.Changed, "#REVERSE_ORDER")
    def _change_reverse_order(self, event: Switch.Changed):
        settings.REVERSE_ORDER = event.value
        settings.save_config()
        self.post_message(ReverseGachaRecord(event.value))
