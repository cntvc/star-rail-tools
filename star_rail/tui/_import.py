from __future__ import annotations

import os
import typing

from textual import on, work
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Static

from star_rail.config import config

from ._footer import Footer
from .handler import error_handler, required_account

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult, RenderResult

    from star_rail.module import HSRClient


class ImportCompleted(Message, bubble=True):
    def __init__(self, cnt: int) -> None:
        super().__init__()
        self.cnt = cnt


class ReturnBtn(Static):
    def render(self) -> RenderResult:
        return "返回主界面"

    def on_click(self) -> None:
        import_screen: ImportScreen = self.app.screen
        import_screen.dismiss(import_screen.cnt)


class FileName(Static):
    file_name: str = reactive("-")

    def render(self):
        return f"文件名: [green]{self.file_name}[/]"


class FileIndicator(Static):
    index: int = reactive(0)
    total: int = reactive(0)

    def render(self) -> RenderResult:
        return f"{self.index} / {self.total}"


class ImportScreen(Screen):
    BINDINGS = [("escape", "exit", "exit import screen")]
    FOOTER_KEY = [ReturnBtn]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file_index = -1
        self.cnt = 0
        self.file_list: list[str] = []

    def compose(self) -> ComposeResult:
        with Container(id="import_view"):
            yield FileName()
            yield FileIndicator()
            yield Button("导入数据", id="import_btn")
            with Horizontal(id="nav_btn"):
                yield Button("上一个", id="prev_button")
                yield Button("下一个", id="next_button")
        yield Footer()

    def on_mount(self) -> None:
        client: HSRClient = self.app.client
        self.file_list = client.get_import_file_list()

        if not self.file_list:
            self.notify("未找到数据文件")
            self.query_one("#import_btn", Button).disabled = True
            self.query_one("#prev_button", Button).disabled = True
            self.query_one("#next_button", Button).disabled = True
        else:
            self.file_index = 0
            self.query_one(FileIndicator).total = len(self.file_list)
            self._update_view(self.file_index)

    def _update_view(self, new_file_index: int):
        if new_file_index <= 0:
            self.query_one("#prev_button", Button).disabled = True
        else:
            self.query_one("#prev_button", Button).disabled = False

        if new_file_index >= len(self.file_list) - 1:
            self.query_one("#next_button", Button).disabled = True
        else:
            self.query_one("#next_button", Button).disabled = False

        self.query_one(FileName).file_name = os.path.basename(self.file_list[new_file_index])
        self.query_one(FileIndicator).index = new_file_index + 1

    @on(Button.Pressed, "#import_btn")
    @work(name="导入数据")
    @error_handler
    @required_account
    async def handle_import_btn(self):
        client: HSRClient = self.app.client
        if config.USE_METADATA and client.metadata_is_latest is False:
            self.notify("请等待 metadata 更新完成")
            return
        file = self.file_list[self.file_index]
        file_info = client.parse_import_file(file)
        if file_info is None:
            self.notify("数据格式错误")
            return

        if file_info.data_type == "SRGF":
            cnt = await client.import_srgf(file_info.data)
        else:
            cnt = await client.import_uigf(file_info.data)

        if cnt == 0:
            self.notify("导入成功，无新增记录")
        else:
            self.notify(f"导入成功, 新增{cnt}条记录")
            self.cnt += cnt

    @on(Button.Pressed, "#prev_button")
    def handle_pressed_prev_btn(self, event: Button.Pressed) -> None:
        event.stop()
        assert self.file_index != -1, "Invalid file_index value"
        self.file_index -= 1
        self._update_view(self.file_index)

    @on(Button.Pressed, "#next_button")
    def handle_pressed_next_btn(self, event: Button.Pressed) -> None:
        event.stop()
        assert self.file_index != -1, "Invalid file_index value"
        self.file_index += 1
        self._update_view(self.file_index)

    def action_exit(self) -> None:
        self.dismiss(self.cnt)
