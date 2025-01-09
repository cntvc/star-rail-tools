from __future__ import annotations

import typing

from textual.containers import Container, Grid, Horizontal, ItemGrid, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Label, TabbedContent, TabPane

from star_rail.module import GACHA_TYPE_DICT

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult

    from star_rail.module import HSRClient
    from star_rail.module.record.model import (
        GachaAnalyzeSummary,
        GachaIndexItem,
        GachaPoolAnalyzeResult,
    )


class RecordDetail(Horizontal):
    def __init__(self, item: GachaIndexItem, index: int, **kwargs):
        super().__init__(**kwargs)
        self._item = item
        self._index = index

    def compose(self) -> ComposeResult:
        self.tooltip = f"{self._item.time}"
        yield Label(f"{self._index}. {self._item.name} ", id="item_name")
        yield Label(f"★ {self._item.index}", id="item_index")


class RecordContent(TabPane):
    def __init__(self, title: str, data: GachaPoolAnalyzeResult, **kwargs):
        super().__init__(title=title, **kwargs)
        self.data = data

    def compose(self) -> ComposeResult:
        if self.data is None:
            yield Container()
            return

        total_count = self.data.total_count
        pity_count = self.data.pity_count
        rank5_count = len(self.data.rank5)
        rank5_average = "-"
        if rank5_count > 0:
            rank5_average = round((total_count - pity_count) / rank5_count, 1)

        with Grid(id="summary"):
            yield Label(f"抽卡总数: {total_count}")
            yield Label(f"五星数量: {rank5_count}")
            yield Label(f"五星平均: {rank5_average}")

        with VerticalScroll() as container:
            container.can_focus = False
            with ItemGrid(id="detail", min_column_width=30):
                with Horizontal(id="pity_item"):
                    yield Label(f"{len(self.data.rank5)+1}. 保底计数 ", id="item_name")
                    yield Label(f"★ {pity_count}", id="item_index")
                rank5 = [RecordDetail(item, index) for index, item in enumerate(self.data.rank5, 1)]
                yield from reversed(rank5)


class RecordView(Container):
    analyze_summary: GachaAnalyzeSummary | None = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        with TabbedContent():
            for gacha_type, name in GACHA_TYPE_DICT.items():
                analyze_result = None
                if self.analyze_summary and not self.analyze_summary.is_empty():
                    analyze_result = self.analyze_summary.get_pool_data(gacha_type)
                yield RecordContent(title=name, id=f"gacha_type_{gacha_type}", data=analyze_result)

    def load_analyze_summary(self):
        client: HSRClient = self.app.client
        self.analyze_summary = client.load_analyze_summary()

    async def refresh_analyze_summary(self):
        client: HSRClient = self.app.client
        self.analyze_summary = await client.refresh_analyze_summary()

    def reset_analyze_summary(self):
        self.analyze_summary = None
