from rich.columns import Columns
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Grid, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static, TabbedContent, TabPane
from textual.worker import Worker, WorkerState

from star_rail.config import settings
from star_rail.module import HSRClient
from star_rail.module.record.model import AnalyzeResult
from star_rail.module.record.types import GACHA_TYPE_DICT, GachaRecordType
from star_rail.tui import events
from star_rail.tui.handler import error_handler, required_account
from star_rail.tui.screens import ExportScreen
from star_rail.tui.widgets import Color, SimpleButton, apply_text_color

RECORD_TMP = """# 抽卡总数: {}\t 5星总数: {}\t 5星平均抽数: {}"""
EMPTY_DATA = [
    r"[O]     \,`/ /      [/O]",
    r"[O]    _)..  `_     [/O]",
    r"[O]   ( __  -\      [/O]",
    r"[O]       '`.       [/O]",
    r"[O]      ( \>_-_,   [/O]",
    r"[O]      _||_ ~-/   [/O]",
]


class EmptyData(Static):
    def render(self) -> RenderableType:
        return apply_text_color(EMPTY_DATA)


class RecordDetail(Container):
    def __init__(self, analyze_result: AnalyzeResult, **kwargs):
        super().__init__(**kwargs)
        self.analyze_result = analyze_result

    def compose(self) -> ComposeResult:
        with TabbedContent():
            for result in self.analyze_result.data:
                tab_id = GachaRecordType.get_by_value(result.gacha_type).name
                tab_name = GACHA_TYPE_DICT[result.gacha_type]

                rank5_count = len(result.rank_5)
                rank5_average = "-"
                if rank5_count:
                    rank5_average = (result.total_count - result.pity_count) / rank5_count
                    rank5_average = round(rank5_average, 2)

                with TabPane(tab_name, id=f"{tab_id}"):
                    yield Static(
                        Markdown(RECORD_TMP.format(result.total_count, rank5_count, rank5_average))
                    )
                    with VerticalScroll():
                        rank_5_list = [
                            Panel(
                                f"{i}. {item.name} : {item.index}抽",
                                expand=True,
                                style=self._gacha_item_color(result.gacha_type, item.index),
                            )
                            for i, item in enumerate(result.rank_5, start=1)
                        ]
                        rank_5_list.append(
                            Panel(
                                f"{len(rank_5_list)+1}. 保底计数 : {result.pity_count}抽",
                                expand=True,
                                style=self._gacha_item_color(result.gacha_type),
                            )
                        )
                        if settings.REVERSE_GACHA_RECORD:
                            rank_5_list.reverse()
                        yield Static(Columns(rank_5_list))

    def _gacha_item_color(self, gacha_type: str, count: int = None):
        """根据抽数进行着色"""
        if not settings.SHOW_LUCK_LEVEL:
            return "none"

        if not count:
            # 默认颜色
            return Color.BLUE

        # 数据统计来源 https://starrailstation.com/cn
        if gacha_type == GachaRecordType.STARTER_WARP.value:
            luck_count = 50
        elif gacha_type == GachaRecordType.LIGHT_CONE_EVENT_WARP.value:
            luck_count = 67
        else:
            luck_count = 74

        if count < luck_count:
            return Color.GREEN
        else:
            return Color.RED


class GachaRecordView(Container):
    analyze_result: reactive[AnalyzeResult] = reactive(None, layout=True)

    def compose(self) -> ComposeResult:
        with Grid():
            yield SimpleButton("刷新记录", id="refresh_with_cache")
            yield SimpleButton("导入记录", id="import_record")
            yield SimpleButton("导出记录", id="export_record")

    async def reverse_record(self):
        """反转跃迁记录"""
        await self._remount_data(self.analyze_result)

    async def show_luck_level(self):
        await self._remount_data(self.analyze_result)

    async def watch_analyze_result(self, new_data: AnalyzeResult):
        await self._remount_data(new_data)

    async def _remount_data(self, data: AnalyzeResult):
        def remove_widgets():
            empty_data = self.query(EmptyData)
            if empty_data:
                empty_data.remove()
            details = self.query(RecordDetail)
            if details:
                details.remove()

        remove_widgets()

        if not data or data.empty():
            await self.mount(EmptyData())
            return
        await self.mount(RecordDetail(data))

    @on(SimpleButton.Pressed, "#refresh_with_cache")
    @work(name="更新跃迁记录")
    @error_handler
    @required_account
    async def handle_refresh_with_webcache(self, event: SimpleButton.Pressed):
        event.stop()
        client: HSRClient = self.app.client

        cnt = await client.refresh_gacha_record("webcache")
        self.analyze_result = await client.display_analysis_results()
        if cnt:
            self.notify(f"新增{cnt}条记录")
        else:
            self.notify("无新记录")

    @on(SimpleButton.Pressed, "#import_record")
    @work()
    @error_handler
    @required_account
    async def handle_import_srgf(self, event: SimpleButton.Pressed):
        event.stop()
        client: HSRClient = self.app.client

        cnt, failed_list = await client.import_gacha_record()
        if cnt:
            self.notify(f"本次导入新增{cnt}条记录")
            self.analyze_result = await client.display_analysis_results()
        else:
            self.notify("本次导入无新增数据")

        if failed_list:
            self.notify("文件导入失败\n---\n" + "\n".join([f"- {name}" for name in failed_list]))

    @on(SimpleButton.Pressed, "#export_record")
    @work()
    @error_handler
    @required_account
    async def handle_export_record(self):
        result = await self.app.push_screen_wait(ExportScreen())
        client: HSRClient = self.app.client
        if result == "export_srgf":
            await client.export_to_srgf()
            self.notify(f"导出成功, 文件位于{client.user.srgf_path.as_posix()}")
        elif result == "export_uigf":
            await client.export_to_uigf()
            self.notify(f"导出成功, 文件位于{client.user.uigf_path.as_posix()}")
        elif result == "export_execl":
            await client.export_to_execl()
            self.notify(f"导出成功, 文件位于{client.user.gacha_record_xlsx_path.as_posix()}")
        else:
            return

    @on(Worker.StateChanged)
    def handle_state_change(self, event: Worker.StateChanged):
        if event.worker.name != "更新跃迁记录":
            return

        state_to_event = {
            WorkerState.RUNNING: events.TaskRunning,
            WorkerState.SUCCESS: events.TaskComplete,
            WorkerState.ERROR: events.TaskError,
            WorkerState.CANCELLED: events.TaskCancel,
        }

        if event_type := state_to_event.get(event.state):
            self.post_message(event_type(event.worker))
