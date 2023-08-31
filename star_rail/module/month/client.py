import typing

from rich import box
from rich.console import Console
from rich.style import Style
from rich.table import Table

from star_rail.database import DataBaseClient
from star_rail.i18n import i18n
from star_rail.utils import console

from ..mihoyo import Account, request
from ..mihoyo.routes import MONTH_INFO_URL
from ..month import converter
from .mapper import MonthInfoMapper
from .model import ApiMonthInfo, MonthInfo


class MonthClient:
    def __init__(self, user: Account) -> None:
        self.user = user

    def fetch_month_info(self, month: str = ""):
        """获取开拓月历

        cookie: cookie_token 为必须包含
        param:
            month 查询月份，为空则查询当月，格式: yyyymm"""

        param = {"uid": self.user.uid, "region": self.user.region, "month": month}

        data = request(
            method="get",
            url=MONTH_INFO_URL.get_url(),
            params=param,
            cookies=self.user.cookie.model_dump("all"),
        )
        return ApiMonthInfo(**data)

    def _save_or_update_month_info(self, month_info: ApiMonthInfo):
        month_info_mapper = converter.api_info_to_mapper(self.user, month_info)
        with DataBaseClient() as db:
            db.insert(month_info_mapper, "update")
            db.insert_batch(converter.reward_source_to_mapper(self.user, month_info), "update")

    def _gen_month_info_tables(self, month_infos: typing.List[MonthInfo]):
        table = Table(
            title=i18n.table.trailblaze_calendar.title,
            box=box.ASCII2,
            title_style=Style(color="blue", bold=True),
        )

        table.add_column(i18n.table.trailblaze_calendar.month)
        for info in month_infos:
            table.add_column(info.month)
        table.add_row(
            i18n.table.trailblaze_calendar.hcoin, *[str(info.hcoin) for info in month_infos]
        )
        table.add_row(
            i18n.table.trailblaze_calendar.rails_pass,
            *[str(info.rails_pass) for info in month_infos]
        )
        return table

    def show_month_info(self):
        default_time_range = 6
        month_info_mappers = MonthInfoMapper.query(self.user.uid, None, default_time_range)
        data = []
        if month_info_mappers:
            data = converter.mapper_to_month_info(month_info_mappers)
        console.clear_all()
        print("UID:", console.color_str("{}".format(self.user.uid), "green"), end="\n\n")
        Console().print(self._gen_month_info_tables(data))

    def refresh_month_info(self):
        cur_month_data = self.fetch_month_info()
        datas = [cur_month_data]
        for month in cur_month_data.optional_month[1:]:
            cur_month_data = self.fetch_month_info(month)
            datas.append(cur_month_data)
        for month_data in datas:
            self._save_or_update_month_info(month_data)
