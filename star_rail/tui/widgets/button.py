from __future__ import annotations

import typing

from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static

if typing.TYPE_CHECKING:
    from textual import events
    from textual.timer import Timer

from time import monotonic

__all__ = ["SimpleButton", "CountdownButton"]


class SimpleButton(Static):
    class Pressed(Message):
        """Event sent when a `Button` is pressed."""

        def __init__(self, button) -> None:
            self.button: SimpleButton = button
            """The button that was pressed."""
            super().__init__()

        @property
        def control(self):
            return self.button

    def on_click(self, event: events.Click):
        event.stop()
        self.post_message(self.Pressed(self))


class CountdownButton(SimpleButton):
    start_time = reactive(monotonic)
    time = reactive(monotonic)
    timer: Timer

    def __init__(self, label: str, count: int, disabled=True, **kwargs):
        super().__init__(**kwargs, disabled=disabled)
        self.label = label
        self.count = count
        self.timer = None

    def on_mount(self):
        self.timer = self.set_interval(1 / 30, self.update_time)

    def update_time(self):
        self.time = monotonic()

    def watch_time(self, time: float):
        second = (time - self.start_time) % 60
        count = self.count - second
        if count <= 0:
            self.disabled = False
            self.timer.stop()
            self.renderable = self.label
        else:
            self.renderable = f"{self.label} ({count:.0f}秒)"
