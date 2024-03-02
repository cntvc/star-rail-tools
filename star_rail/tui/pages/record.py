from rich.columns import Columns
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Grid, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static, TabbedContent, TabPane

from star_rail.config import settings
from star_rail.module import HSRClient
from star_rail.module.record.model import AnalyzeResult
from star_rail.module.record.types import GACHA_TYPE_DICT, GachaRecordType
from star_rail.tui.handler import error_handler, required_account
from star_rail.tui.widgets import SimpleButton, apply_text_color

RECORD_TMP = """# 抽卡总数: {}\t 5星总数: {}\t 5星平均抽数: {}"""
EMPTY_DATA = [
    r"[O]     \,`/ /      [/O]",
    r"[O]    _)..  `_     [/O]",
    r"[O]   ( __  -\      [/O]",
    r"[O]       '`.       [/O]",
    r"[O]      ( \>_-_,   [/O]",
    r"[O]      _||_ ~-/   [G]No data at the moment![/G][/O]",
]


class EmptyData(Static):
    def render(self) -> RenderableType:
        return apply_text_color(EMPTY_DATA)


class RecordDetail(Container):
    def __init__(self, analyze_result: AnalyzeResult, **kwargs):
        super().__init__(**kwargs)
        self.analyze_result = analyze_result

    def compose(self) -> RenderableType:
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
                    #
                    with VerticalScroll():
                        rank_5_list = [
                            Panel(f"{i}. {item.name} : {item.index}抽", expand=True)
                            for i, item in enumerate(result.rank_5, start=1)
                        ]
                        rank_5_list.append(
                            Panel(f"{len(rank_5_list)+1}. 保底计数 : {result.pity_count}抽", expand=True)
                        )
                        if settings.REVERSE_ORDER:
                            rank_5_list.reverse()
                        yield Static(Columns(rank_5_list))


class GachaRecordDialog(Container):
    analyze_result: reactive[AnalyzeResult] = reactive(None, layout=True)

    def compose(self) -> ComposeResult:
        with Grid():
            yield SimpleButton("刷新记录", id="refresh_with_cache")
            # yield SimpleButton("读取链接", id="refresh_with_url")
            yield SimpleButton("导入数据", id="import")
            yield SimpleButton("生成Execl", id="export_execl")
            yield SimpleButton("生成SRGF", id="export_srgf")

    async def reverse_record(self):
        """反转显示跃迁记录"""
        if self.query(EmptyData):
            return
        details = self.query(RecordDetail)
        if details:
            details.remove()
        await self.mount(RecordDetail(self.analyze_result))

    async def watch_analyze_result(self, new: AnalyzeResult):
        def remove_widgets():
            empty_data = self.query(EmptyData)
            if empty_data:
                empty_data.remove()
            details = self.query(RecordDetail)
            if details:
                details.remove()

        remove_widgets()

        if not new or new.empty():
            self.mount(EmptyData(id="empty_record"))
            return
        await self.mount(RecordDetail(new))

    @on(SimpleButton.Pressed, "#refresh_with_cache")
    @work()
    @error_handler
    @required_account
    async def refresh_with_webcache(self):
        client: HSRClient = self.app.client
        self.notify("正在更新数据")
        await client.refresh_gacha_record("webcache")
        self.analyze_result = await client.view_analysis_results()
        self.notify("更新已完成")

    @on(SimpleButton.Pressed, "#refresh_with_url")
    @work()
    @error_handler
    @required_account
    async def refresh_with_url(self):
        client: HSRClient = self.app.client
        self.notify("正在更新数据")
        await client.refresh_gacha_record("clipboard")
        self.analyze_result = await client.view_analysis_results()
        self.notify("更新已完成")

    async def view_record(self):
        client: HSRClient = self.app.client
        self.analyze_result = await client.view_analysis_results()

    @on(SimpleButton.Pressed, "#import")
    @work()
    @error_handler
    @required_account
    async def import_srgf(self):
        client: HSRClient = self.app.client
        cnt, failed_list = await client.import_srgf_json()
        if cnt:
            self.notify(f"新增{cnt}条记录")
        else:
            self.notify("无数据可导入")
        if failed_list:
            self.notify("\n".join([f"文件{name }导入失败" for name in failed_list]))

    @on(SimpleButton.Pressed, "#export_execl")
    @work()
    @error_handler
    @required_account
    async def export_to_execl(self):
        client: HSRClient = self.app.client
        await client.export_to_execl()
        self.notify(f"导出成功, 文件位于{client.user.gacha_record_xlsx_path.as_posix()}")

    @on(SimpleButton.Pressed, "#export_srgf")
    @work()
    @error_handler
    @required_account
    async def export_to_srgf(self):
        client: HSRClient = self.app.client
        await client.export_to_srgf()
        self.notify(f"导出成功, 文件位于{client.user.srgf_path.as_posix()}")
