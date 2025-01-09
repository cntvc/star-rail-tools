from __future__ import annotations

import typing

from textual import on
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Markdown, Static

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult, RenderResult

    from star_rail.module import HSRClient
    from star_rail.module.record.record import FileInfo


class BackMain(Static):
    def render(self) -> RenderResult:
        return "返回主界面"

    def on_click(self) -> None:
        self.app.pop_screen()


class ImportFooter(Horizontal):
    def compose(self) -> ComposeResult:
        yield BackMain()


FILE_DETAIL_TEMP = """
### 文件名: {}
- 类型: {} {}
- 时间: {}
- App: {}_{}
- 数量: {}
"""


class FileDetailView(Container):
    file_info: FileInfo = reactive(None, recompose=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        if self.file_info:
            name = self.file_info.name
            data_type = self.file_info.data_type
            data = self.file_info.data
            data_version = data.info.version if data_type == "UIGF" else data.info.srgf_version
            export_time = data.info.export_time
            export_app = self.file_info.data.info.export_app
            export_app_version = self.file_info.data.info.export_app_version
            data_count = len(data.list) if data_type == "SRGF" else len(data.hkrpg[0].list)
        else:
            name = ""
            data_type = ""
            data_version = ""
            export_time = ""
            export_app = ""
            export_app_version = ""
            data_count = 0
        yield Markdown(
            FILE_DETAIL_TEMP.format(
                name,
                data_type,
                data_version,
                export_time,
                export_app,
                export_app_version,
                data_count,
            ),
            id="file_detail",
        )
        yield Button("导入数据", id="import_btn")

    @on(Button.Pressed, "#import_btn")
    async def handle_import_btn(self):
        client: HSRClient = self.app.client
        if self.file_info.data_type == "srgf":
            cnt = await client.import_srgf(self.file_info.data)
        else:
            cnt = await client.import_uigf(self.file_info.data)
        self.notify(f"导入成功，新增{cnt}条记录")


class FileIndicator(Static):
    index: int = reactive(0)
    total: int = reactive(0)

    def render(self) -> RenderResult:
        return f"{self.index} / {self.total}"


class ImportScreen(Screen):
    BINDINGS = [("escape", "exit", "exit import screen")]

    file_info_list: list[FileInfo] = reactive([])

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.file_index = -1

    def compose(self) -> ComposeResult:
        with Container(id="import_view"):
            yield FileDetailView()
            yield FileIndicator()
            with Horizontal(id="nav_btn"):
                yield Button("上一个", id="prev_button")
                yield Button("下一个", id="next_button")
        yield ImportFooter()

    def on_mount(self) -> None:
        client: HSRClient = self.app.client
        file_list = client.get_import_file_list()
        if not file_list:
            return

        result_list = []
        for file in file_list:
            info = client.parse_import_file(file)
            if info is None:
                continue
            result_list.append(info)

        self.file_info_list = result_list
        if self.file_info_list:
            self.file_index = 0
            self._update_view(self.file_index)
            self.query_one(FileIndicator).total = len(self.file_info_list)

    def _update_view(self, new_file_index: int):
        if new_file_index <= 0:
            self.query_one("#prev_button").disabled = True
        else:
            self.query_one("#prev_button").disabled = False
        if new_file_index >= len(self.file_info_list) - 1:
            self.query_one("#next_button").disabled = True
        else:
            self.query_one("#next_button").disabled = False

        self.query_one(FileDetailView).file_info = self.file_info_list[new_file_index]
        self.query_one(FileIndicator).index = new_file_index + 1

    @on(Button.Pressed, "#prev_button")
    def handle_pressed_prev_btn(self) -> None:
        assert self.file_index != -1, "Invalid file_index value"
        self.file_index -= 1
        self._update_view(self.file_index)

    @on(Button.Pressed, "#next_button")
    def handle_pressed_next_btn(self) -> None:
        assert self.file_index != -1, "Invalid file_index value"
        self.file_index += 1
        self._update_view(self.file_index)

    def action_exit(self) -> None:
        self.app.pop_screen()
