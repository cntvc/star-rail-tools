import traceback

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, DataTable

from star_rail import exceptions as error
from star_rail.module import HSRClient
from star_rail.utils.logger import logger


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
    async def refresh_month_info(self):
        client: HSRClient = self.app.client
        try:
            cnt = await client.refresh_month_info()
        except error.HsrException as e:
            self.notify(e.msg, severity="warning")
            return
        except Exception as e:
            logger.debug(traceback.format_exc())
            self.notify(str(e), severity="error")
            return
        if cnt:
            msg = f"已成功刷新最近{cnt}月数据"
        else:
            msg = "暂无新数据"
        self.notify(msg)

    @work(exclusive=True)
    @on(Button.Pressed, "#view")
    async def view_month_info(self):
        client: HSRClient = self.app.client
        try:
            info_list = await client.get_month_info_in_range()
        except error.HsrException as e:
            self.notify(e.msg, severity="warning")
            return
        except Exception as e:
            logger.debug(traceback.format_exc())
            self.notify(str(e), severity="error")
            return
        if not info_list:
            self.notify("无数据")
            return
        table = self.query_one(DataTable)
        table.clear(columns=True)
        columns_name = ["月份", "星穹", "列车票"]
        rows = [(item.month, item.hcoin, item.rails_pass) for item in info_list]
        table.add_columns(*columns_name)
        table.add_rows(rows)
