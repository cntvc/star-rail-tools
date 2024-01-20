from textual.message import Message
from textual.widgets import Static

__all__ = ["SimpleButton"]


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

    def on_click(self):
        self.post_message(self.Pressed(self))
