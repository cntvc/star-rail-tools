from rich.console import RenderableType
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static


class CurrentUID(Static):
    uid = reactive("", layout=True)

    def render(self) -> RenderableType:
        return "UID : 未登陆" if not self.uid else f"UID : {self.uid}"


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield CurrentUID()
