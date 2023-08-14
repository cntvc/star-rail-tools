import typing

from prettytable import PrettyTable

from star_rail.core import DBClient
from star_rail.i18n import i18n
from star_rail.utils import functional

from ..mihoyo.account import Account
from ..mihoyo.api_client import request
from ..mihoyo.routes import MONTH_INFO_URL
from .converter import info_to_mapper, reward_source_to_mapper
from .mapper import MonthInfoMapper
from .model import MonthInfo


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
        return MonthInfo(**data)

    def _save_or_update_month_info(self, month_info: MonthInfo):
        month_info_mapper = info_to_mapper(self.user, month_info)
        with DBClient() as db:
            db.insert(month_info_mapper, "update")
            db.insert_batch(reward_source_to_mapper(self.user, month_info), "update")

    def _gen_month_info_tables(self, month_infos: typing.List[MonthInfoMapper]):
        month_info_table = PrettyTable()

        month_info_table.align = "l"
        month_info_table.title = i18n.table.trailblaze_calendar.title
        month_info_table.add_column(
            i18n.table.trailblaze_calendar.month,
            [i18n.table.trailblaze_calendar.hcoin, i18n.table.trailblaze_calendar.rails_pass],
        )
        for item in month_infos:
            month_info_table.add_column(item.month, [item.hcoin, item.rails_pass])
        return month_info_table

    def visualization(self, data: typing.List[MonthInfoMapper]):
        functional.clear_screen()
        print("UID:", functional.color_str("{}".format(self.user.uid), "green"))
        print(self._gen_month_info_tables(data))

    def refresh_month_info(self):
        cur_month_data = self.fetch_month_info()
        datas = []
        datas.append(cur_month_data)
        for month in cur_month_data.optional_month[1:]:
            cur_month_data = self.fetch_month_info(month)
            datas.append(cur_month_data)
        for month_data in datas:
            self._save_or_update_month_info(month_data)
