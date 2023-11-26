from rich.console import RenderableType
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Static, TabbedContent, TabPane

from star_rail.config import settings
from star_rail.module import HSRClient
from star_rail.module.record.model import AnalyzeResult
from star_rail.module.record.types import GACHA_TYPE_DICT, GachaRecordType


class GachaContent(Horizontal):
    def __init__(self, desc: str, val, **kwargs):
        super().__init__(**kwargs)
        self.desc = desc
        self.val = val

    def compose(self) -> ComposeResult:
        yield Static(self.desc, id="desc")
        yield Static(self.val, id="value")


class RecordDetail(Container):
    def __init__(self, analyze_result: AnalyzeResult, **kwargs):
        super().__init__(**kwargs)
        self.analyze_result = analyze_result

    def compose(self) -> RenderableType:
        if self.analyze_result is None:
            return
        yield Static(f"数据更新时间:{self.analyze_result.update_time}")
        with TabbedContent():
            for result in self.analyze_result.data:
                if (
                    not settings.DISPLAY_STARTER_WARP
                    and result.gacha_type == GachaRecordType.STARTER_WARP.value
                ):
                    continue
                name = GACHA_TYPE_DICT[result.gacha_type]
                with TabPane(name):
                    yield GachaContent("抽卡总数", f"{result.total_count}")
                    yield GachaContent("5星总数", f"{len(result.rank_5)}")
                    yield GachaContent("保底计数", f"{result.pity_count}")
                    yield Static("===================================")
                    with VerticalScroll():
                        for item in result.rank_5:
                            yield GachaContent(item.name, f"{item.index}抽")


class GachaRecordDialog(Container):
    analyze_result: reactive[AnalyzeResult] = reactive(None, layout=True)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Button("刷新记录", id="refresh_with_cache")
            # yield Button("读取链接", id="refresh_with_url")
            yield Button("查看统计", id="view_record")
            yield Button("导入数据", id="import")
            yield Button("生成Execl", id="export_execl")
            yield Button("生成SRGF", id="export_srgf")
        yield RecordDetail(None)

    def watch_analyze_result(self, new):
        details = self.query(RecordDetail)
        if details:
            details.remove()
        self.mount(RecordDetail(new))

    @work(exclusive=True)
    @on(Button.Pressed, "#refresh_with_cache")
    async def refresh_with_webcache(self):
        client: HSRClient = self.app.client
        await client.refresh_gacha_record("webcache")
        self.analyze_result = await client.view_analysis_results()

    @work(exclusive=True)
    @on(Button.Pressed, "#refresh_with_url")
    async def refresh_with_url(self):
        client: HSRClient = self.app.client
        await client.refresh_gacha_record("clipboard")

    @work(exclusive=True)
    @on(Button.Pressed, "#view_record")
    async def view_record(self):
        client: HSRClient = self.app.client
        self.analyze_result = await client.view_analysis_results()

    @work(exclusive=True)
    @on(Button.Pressed, "#import")
    async def import_srgf(self):
        client: HSRClient = self.app.client
        cnt, failed_list = await client.import_srgf_json()
        if cnt:
            self.notify(f"新增{cnt}条记录")
        if failed_list:
            self.notify("\n".join([f"文件{name }导入失败" for name in failed_list]))

    @work(exclusive=True)
    @on(Button.Pressed, "#export_execl")
    async def export_to_execl(self):
        client: HSRClient = self.app.client
        await client.export_to_execl()
        self.notify("导出成功")

    @work(exclusive=True)
    @on(Button.Pressed, "#export_srgf")
    async def export_to_srgf(self):
        client: HSRClient = self.app.client
        await client.export_to_srgf()
        self.notify("导出成功")
