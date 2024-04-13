from rich.console import RenderableType
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import ProgressBar, Static

__all__ = ["StatusBar", "CurrentUID"]


class CurrentUID(Static):
    uid = reactive("", layout=True)

    def render(self) -> RenderableType:
        return "UID : 未登陆" if not self.uid else f"UID : {self.uid}"


class Notice(Static):

    def render(self) -> RenderableType:
        return "通知"

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.app._toggle_sidebar()


class TaskStatus(Horizontal):
    def compose(self) -> ComposeResult:
        yield Static(self.name, id="task_name")
        yield ProgressBar(show_percentage=False, show_eta=False)

    def update(self, name: str):
        self.name = name
        self.query_one("#task_name", Static).update(name)


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield CurrentUID()
        yield Horizontal(id="progress_status")
        yield Notice()

    def add_task_bar(self, **kwargs):
        self.query_one("#progress_status", Horizontal).mount(TaskStatus(**kwargs))

    def remove_task_bar(self):
        self.query_one("#progress_status > TaskStatus", TaskStatus).remove()

    def update_task_bar(self, name: str):

        task_bar = self.query_one("#progress_status", Horizontal)
        if task_status := task_bar.query(TaskStatus):
            task_status.first().update(name)
