from __future__ import annotations

import typing

from rich.markdown import Markdown
from textual import on
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Static

from star_rail.tui.widgets import SimpleButton

if typing.TYPE_CHECKING:
    from star_rail.tui.widgets import HSRNotification

__all__ = ["NotificationDetail"]


class NotificationDetail(ModalScreen[bool]):
    BINDINGS = [("escape", "close", "Close notification")]

    def __init__(self, notification: HSRNotification):
        super().__init__()
        self.notification = notification

    def compose(self) -> ComposeResult:
        with Grid():
            yield Static(Markdown(self.notification.content), id="content")
            yield SimpleButton("关闭", id="close")

    @on(SimpleButton.Pressed, "#close")
    def action_close(self):
        self.app.pop_screen()
