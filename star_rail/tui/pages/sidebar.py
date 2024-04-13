from textual import on
from textual.app import ComposeResult
from textual.containers import Container

from star_rail.tui.widgets import NotificationList, SimpleButton

__all__ = ["Sidebar"]


class Sidebar(Container):
    BORDER_TITLE = "通知"
    def compose(self) -> ComposeResult:
        yield NotificationList()
        with Container(id="buttons"):
            yield SimpleButton("清空", id="clear")
            yield SimpleButton("返回", id="hide")

    @on(SimpleButton.Pressed, "#clear")
    def clear(self, event: SimpleButton.Pressed):
        event.stop()
        self.query_one(NotificationList).clear()

    @on(SimpleButton.Pressed, "#hide")
    def hide_sidebar(self, event: SimpleButton.Pressed):
        event.stop()
        self.screen.set_focus(None)
        self.add_class("-hidden")
