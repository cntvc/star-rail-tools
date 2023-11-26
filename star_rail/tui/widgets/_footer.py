from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class CurrentUID(Static):
    uid = reactive("未设置")

    def render(self) -> RenderableType:
        return f"{self.uid}"


class CurrentAccount(Horizontal):
    uid = reactive("未设置")

    def compose(self) -> ComposeResult:
        yield Static("当前账户:", id="account_desc")
        yield CurrentUID(id="current_uid")


class Footer(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Ctrl+B:关于")
        yield CurrentAccount()
