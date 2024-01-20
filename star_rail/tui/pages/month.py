from rich.markdown import Markdown
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Center, Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Select, Static

from star_rail.module import HSRClient
from star_rail.module.month.model import MonthInfoItem
from star_rail.tui.handler import error_handler, required_account
from star_rail.tui.widgets import SimpleButton, apply_text_color

DETAIL_TEMP = """

- 星琼 : {}
- 星轨通票&星轨专票 : {}

---
|来源|占比|
|:----|----:|
{}
"""

EMPTY_DATA = [
    r"[O]     \,`/ /      [/O]",
    r"[O]    _)..  `_     [/O]",
    r"[O]   ( __  -\      [/O]",
    r"[O]       '`.       [/O]",
    r"[O]      ( \>_-_,   [/O]",
    r"[O]      _||_ ~-/   [G]No data at the moment![/G][/O]",
]


class MonthInfoDetail(VerticalScroll):
    def __init__(self, month_detail: MonthInfoItem, **kwargs):
        super().__init__(**kwargs)
        self.month_detail = month_detail

    def compose(self) -> ComposeResult:
        with Center():
            yield Static(
                Markdown(
                    DETAIL_TEMP.format(
                        self.month_detail.hcoin,
                        self.month_detail.rails_pass,
                        "\n".join(
                            [
                                f"|{source.action_name}|{source.percent}%|"
                                for source in self.month_detail.source
                            ]
                        ),
                    )
                )
            )


class MonthList(Select):
    pass


class EmptyData(Container):
    def compose(self) -> ComposeResult:
        with Center():
            yield Static(apply_text_color(EMPTY_DATA))


class MonthDialog(Container):
    month_info_list: reactive[list[MonthInfoItem]] = reactive([], layout=True)

    def compose(self) -> ComposeResult:
        yield SimpleButton("刷新", id="refresh")

    @work(exclusive=True)
    @on(SimpleButton.Pressed, "#refresh")
    @error_handler
    @required_account
    async def refresh_month_info(self):
        client: HSRClient = self.app.client
        if client.user.cookie.empty():
            self.notify("请设置Cookie后再试")
            return
        cnt = await client.refresh_month_info()
        self.notify(f"已更新最近{cnt}月的数据")
        self.month_info_list = await client.get_month_info_in_range()

    def watch_month_info_list(self, new: list[MonthInfoItem]):
        def remove_widgets():
            empty_data = self.query(EmptyData)
            if empty_data:
                empty_data.remove()

            g_month_info = self.query(MonthList)
            if g_month_info:
                g_month_info.remove()

            detail = self.query(MonthInfoDetail)
            if detail:
                detail.remove()

        remove_widgets()

        # 空数据加载默认组件
        if not new:
            self.mount(EmptyData(id="empty_month"))
            return

        month_list = [item.month for item in self.month_info_list]
        self.mount(
            MonthList(
                [(x, i) for i, x in enumerate(month_list)], prompt=month_list[0], allow_blank=False
            )
        )
        self.mount(MonthInfoDetail(new[0]))

    @on(Select.Changed)
    def select_month(self, event: Select.Changed):
        detail = self.query(MonthInfoDetail)
        if detail:
            detail.remove()
        self.mount(MonthInfoDetail(self.month_info_list[event.value]))
