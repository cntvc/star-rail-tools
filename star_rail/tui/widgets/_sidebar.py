from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Switch

from star_rail import __version__ as version


class OptionGroup(Container):
    pass


class Title(Static):
    pass


class Message(Static):
    pass


ABOUT_MESSAGE = """
欢迎使用 StarRailTools

作者: cntvc

邮箱: cntvc@outlook.com

[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]GitHub 仓库主页[/]

[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]

[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]
"""


class DarkSwitch(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static("Dark mode toggle", classes="label")
        yield Switch(value=self.app.dark)

    def on_mount(self) -> None:
        self.watch(self.app, "dark", self.on_dark_change, init=False)

    def on_dark_change(self) -> None:
        self.query_one(Switch).value = self.app.dark

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.app.dark = event.value


class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]v{version}"


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("StarRailTools")
        yield OptionGroup(Message(ABOUT_MESSAGE), Version())
        yield DarkSwitch()
