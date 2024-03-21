from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Switch

from star_rail.config import settings
from star_rail.tui.events import ReverseGachaRecord, ShowLuckLevel


class ConfigDialog(Container):
    def compose(self) -> ComposeResult:
        yield ConfigSwitchItem(
            switch_id="CHECK_UPDATE", desc="自动检测更新", status=settings.CHECK_UPDATE
        )
        yield ConfigSwitchItem(
            switch_id="REVERSE_GACHA_RECORD",
            desc="倒序显示跃迁记录",
            status=settings.REVERSE_GACHA_RECORD,
        )
        yield ConfigSwitchItem(
            switch_id="SHOW_LUCK_LEVEL", desc="显示欧非程度", status=settings.SHOW_LUCK_LEVEL
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
    def handle_check_update(self, event: Switch.Changed):
        settings.CHECK_UPDATE = event.value
        settings.save_config()

    @on(Switch.Changed, "#REVERSE_GACHA_RECORD")
    def handle_reverse_gacha_record(self, event: Switch.Changed):
        settings.REVERSE_GACHA_RECORD = event.value
        settings.save_config()
        self.post_message(ReverseGachaRecord(event.value))

    @on(Switch.Changed, "#SHOW_LUCK_LEVEL")
    def handle_show_luck_level(self, event: Switch.Changed):
        settings.SHOW_LUCK_LEVEL = event.value
        settings.save_config()
        self.post_message(ShowLuckLevel(event.value))
