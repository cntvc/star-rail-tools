from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, DataTable

from star_rail.module import HSRClient
from star_rail.tui.handler import error_handler, required_account


class MonthInfo(Container):
    def compose(self) -> ComposeResult:
        return super().compose()


class MonthDialog(Container):
    def compose(self) -> ComposeResult:
        yield Button("查看", id="view")
        yield Button("刷新", id="refresh")
        with VerticalScroll():
            yield DataTable()

    @work(exclusive=True)
    @on(Button.Pressed, "#refresh")
    @error_handler
    @required_account
    async def refresh_month_info(self):
        client: HSRClient = self.app.client
        if client.user.cookie.empty():
            self.notify("请设置Cookie后再试")
            return
        cnt = await client.refresh_month_info()
        self.notify(f"已成功刷新最近{cnt}月数据")

    @work(exclusive=True)
    @on(Button.Pressed, "#view")
    @error_handler
    @required_account
    async def view_month_info(self):
        client: HSRClient = self.app.client
        info_list = await client.get_month_info_in_range()
        if not info_list:
            self.notify("暂无数据")
            return
        table = self.query_one(DataTable)
        table.clear(columns=True)
        columns_name = ["月份", "星穹", "列车票"]
        rows = [(item.month, item.hcoin, item.rails_pass) for item in info_list]
        table.add_columns(*columns_name)
        table.add_rows(rows)
