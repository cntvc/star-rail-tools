import typing

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Select, Static, Switch

from star_rail.config import settings


class ConfigDialog(Container):
    def compose(self) -> ComposeResult:
        yield ConfigSwitchItem("CHECK_UPDATE", "自动检测更新", settings.CHECK_UPDATE)
        yield ConfigSwitchItem("DISPLAY_STARTER_WARP", "显示新手池数据", settings.DISPLAY_STARTER_WARP)
        # yield ConfigSelectItem(
        #     "LANGUAGE", "语言", [("中文", "zh-cn"), ("English", "en-us")], settings.LANGUAGE
        # )


class ConfigSelectItem(Horizontal):
    def __init__(
        self, id: str, desc: str, options: typing.Iterable, default: str, **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.desc = desc
        self.options = options
        self.default = default

    def compose(self) -> ComposeResult:
        yield Static(self.desc)
        yield Select(options=self.options, allow_blank=False, value=self.default)

    @on(Select.Changed)
    def update_settings(self, event: Select.Changed):
        settings.update_config({self.id: event.value})
        settings.save_config()


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
