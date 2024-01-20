from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from star_rail import __version__ as version


class OptionGroup(Container):
    pass


class Title(Static):
    pass


class Message(Static):
    pass


ABOUT_MESSAGE = """
作者: cntvc

邮箱: cntvc@outlook.com

[@click="app.open_link('https://github.com/cntvc/star-rail-tools')"]GitHub 仓库主页[/]

[@click="app.open_link('https://github.com/cntvc/star-rail-tools/releases')"]下载链接[/]

[@click="app.open_link('https://github.com/cntvc/star-rail-tools/issues')"]Bug 反馈[/]
"""


class Version(Static):
    def render(self) -> RenderableType:
        return f"[b]v{version}"


class Sidebar(Container):
    def compose(self) -> ComposeResult:
        yield Title("StarRailTools")
        with OptionGroup():
            yield Message(ABOUT_MESSAGE)
            yield Version()
