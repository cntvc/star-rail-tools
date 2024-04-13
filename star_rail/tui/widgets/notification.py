import random
import string
from uuid import uuid4

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widgets import Static

from star_rail.tui.widgets import SimpleButton
from star_rail.utils.date import Date

__all__ = ["HSRNotification", "NotificationItem", "NotificationList"]


class HSRNotification:
    id: str
    """id"""
    timestamp: int
    """时间戳"""
    time: str
    content: str
    """消息内容"""
    title: str
    clickable: bool = True

    def __init__(self, notification: str, title: str = "", clickable: bool = True):
        _time = Date.now()
        self.timestamp = int(_time.timestamp())
        self.time = Date.format_time(_time)
        self.content = notification
        self.title = title
        self.id = self.genetate_id()
        self.clickable = clickable

    def genetate_id(self):
        prefix = random.choice(string.ascii_letters)
        uuid_str = str(uuid4())
        # 确保id不以数字开头
        return prefix + uuid_str[1:]


class NotificationContent(Static):
    def __init__(self, notification: HSRNotification, **kwargs) -> None:
        super().__init__(**kwargs)
        self.notification = notification

    def render(self):
        return f"{self.notification.time}\n\n{self.notification.content}"

    async def on_click(self, event: events.Click):
        event.stop()
        """打开窗口显示消息详情"""
        if not self.notification.clickable:
            return

        # circular import
        from star_rail.tui.screens.notification_detail import NotificationDetail

        self.app.push_screen(NotificationDetail(self.notification))


class NotificationItem(Horizontal):
    class Delete(Message):
        def __init__(self, item) -> None:
            self.item: NotificationItem = item
            """The button that was pressed."""
            super().__init__()

        @property
        def control(self):
            return self.item

    def __init__(self, notification: HSRNotification, **kwargs) -> None:
        super().__init__(id=notification.id, **kwargs)
        self.notification = notification

    def compose(self) -> ComposeResult:
        yield NotificationContent(self.notification)
        yield SimpleButton("删除", id="delete")

    @on(SimpleButton.Pressed, "#delete")
    def delete(self, event: SimpleButton.Pressed):
        event.stop()

        self.post_message(NotificationItem.Delete(self))


class NotificationList(VerticalScroll):

    def add(self, notification: HSRNotification):
        list_widget = self.query("NotificationItem")
        if 0 == len(list_widget):
            self.mount(NotificationItem(notification))
        else:
            self.mount(NotificationItem(notification), before=list_widget.first())

    def clear(self):
        await_remove = self.query("NotificationList > NotificationItem").remove()
        return await_remove

    @on(NotificationItem.Delete)
    def delete(self, event: NotificationItem.Delete):
        event.stop()
        await_remove = self.query(f"#{event.item.notification.id}").remove()
        return await_remove
