import typing

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Select, Static, Switch

from star_rail.config import settings
from star_rail.tui.events import ReverseGachaRecord, ShowLuckLevel


class ConfigView(VerticalScroll):
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
        yield SelectBox(
            select_id="metadata_lang",
            desc="Metadata 默认语言",
            default=settings.METADATA_LANG,
            options=[("简体中文", "zh-cn"), ("English", "en-us")],
            tips="设置导入跃迁记录时的默认处理语言。\n当导入的数据缺少 lang 等相关字段数据时使用该设置项的数据补齐",
        )
        yield SelectBox(
            select_id="record_update_mode",
            desc="跃迁记录更新方式",
            default=settings.RECORD_UPDATE_MODE,
            options=[("增量更新", "incremental"), ("全量更新", "full")],
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
        event.stop()
        settings.CHECK_UPDATE = event.value
        settings.save_config()

    @on(Switch.Changed, "#REVERSE_GACHA_RECORD")
    def handle_reverse_gacha_record(self, event: Switch.Changed):
        event.stop()
        settings.REVERSE_GACHA_RECORD = event.value
        settings.save_config()
        self.post_message(ReverseGachaRecord(event.value))

    @on(Switch.Changed, "#SHOW_LUCK_LEVEL")
    def handle_show_luck_level(self, event: Switch.Changed):
        event.stop()
        settings.SHOW_LUCK_LEVEL = event.value
        settings.save_config()
        self.post_message(ShowLuckLevel(event.value))


class SelectBox(Horizontal):
    def __init__(
        self,
        select_id: str,
        desc: str,
        default,
        options: list[tuple[str, typing.Any]],
        tips: str = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.select_id = select_id
        self.desc = desc
        self.default = default
        self.options = options
        self.tips = tips

    def compose(self) -> ComposeResult:
        desc = Static(self.desc)
        if self.tips:
            desc.tooltip = self.tips
        yield desc
        yield Select(options=self.options, value=self.default, allow_blank=False, id=self.select_id)

    @on(Select.Changed, "#metadata_lang")
    def handle_switch_metadata_lang(self, event: Select.Changed):
        event.stop()
        settings.METADATA_LANG = str(event.value)
        settings.save_config()

    @on(Select.Changed, "#record_update_mode")
    def handle_switch_record_update_mode(self, event: Select.Changed):
        event.stop()
        settings.RECORD_UPDATE_MODE = str(event.value)
        settings.save_config()
