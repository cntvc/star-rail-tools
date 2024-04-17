from rich.console import RenderableType
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.reactive import reactive
from textual.widgets import ListItem, ListView, Markdown, Static

from star_rail import exceptions as error
from star_rail.module import HSRClient
from star_rail.module.month.model import MonthInfoItem
from star_rail.module.types import GameBiz
from star_rail.tui.handler import error_handler, required_account
from star_rail.tui.widgets import SimpleButton, apply_text_color

DETAIL_TEMP = """
##### 月份 : {}

- 星琼 : {}
- 星轨通票&星轨专票 : {}

|来源|占比|数量|
|:----|:----:|----:|
{}
"""

EMPTY_DATA = [
    r"[O]     \,`/ /      [/O]",
    r"[O]    _)..  `_     [/O]",
    r"[O]   ( __  -\      [/O]",
    r"[O]       '`.       [/O]",
    r"[O]      ( \>_-_,   [/O]",
    r"[O]      _||_ ~-/   [/O]",
]


class MonthInfoDetail(Container):
    def __init__(self, month_item: MonthInfoItem, **kwargs):
        super().__init__(**kwargs)
        self.month_item = month_item

    def compose(self) -> ComposeResult:
        yield Markdown(
            DETAIL_TEMP.format(
                self.month_item.month,
                self.month_item.hcoin,
                self.month_item.rails_pass,
                "\n".join(
                    [
                        f"|{source.action_name}|{source.percent}%|{source.num}|"
                        for source in self.month_item.source
                    ]
                ),
            )
        )


class MonthList(ListView):
    def __init__(self, month_list: list[str], **kwargs):
        super().__init__(**kwargs)
        self.month_list = month_list

    def compose(self) -> ComposeResult:
        for month in self.month_list[::-1]:
            yield ListItem(Static(month), name=month)


class MonthInfo(Grid):
    def __init__(self, month_info: dict[str, MonthInfoItem], **kwargs):
        super().__init__(**kwargs)
        self.month_info = month_info
        # 这里是时间顺序
        self.month_list = [month for month in sorted(self.month_info.keys())]

    def compose(self) -> ComposeResult:
        yield MonthList(self.month_list)

    @on(ListView.Highlighted)
    def handle_listview_select(self, event: ListView.Highlighted):
        event.stop()
        detail = self.query(MonthInfoDetail)
        if detail:
            detail.remove()

        self.mount(MonthInfoDetail(self.month_info[event.item.name]))


class EmptyData(Static):
    def render(self) -> RenderableType:
        return apply_text_color(EMPTY_DATA)


class MonthDialog(Container):
    month_info: dict[str, MonthInfoItem] = reactive({})

    def compose(self) -> ComposeResult:
        yield SimpleButton("刷新", id="refresh")

    @on(SimpleButton.Pressed, "#refresh")
    @work()
    @error_handler
    @required_account
    async def handle_refresh_month_info(self, event: SimpleButton.Pressed):
        event.stop()
        client: HSRClient = self.app.client
        if client.user.game_biz == GameBiz.GLOBAL:
            raise error.HsrException("暂不支持国际服账号")

        if client.user.cookie.empty():
            self.notify("请设置Cookie后再试")
            return
        cnt = await client.refresh_month_info()
        self.notify(f"已更新最近{cnt}月的数据")
        await self.refresh_data()

    async def refresh_data(self):
        client: HSRClient = self.app.client
        month_info_list = await client.get_month_info_history()
        self.month_info = {item.month: item for item in month_info_list}

    def watch_month_info(self, new: list[MonthInfoItem]):
        def remove_widgets():
            empty_data = self.query(EmptyData)
            if empty_data:
                empty_data.remove()

            month_info = self.query(MonthInfo)
            if month_info:
                month_info.remove()

        remove_widgets()

        # 空数据加载默认组件
        if not new:
            self.mount(EmptyData(id="empty_month"))
            return

        self.mount(MonthInfo(self.month_info))
