import typing

from prettytable import PrettyTable

from star_rail.database import convert, db
from star_rail.utils import functional

from ..mihoyo.account import Account
from ..mihoyo.api_client import request
from ..mihoyo.routes import MONTH_INFO_URL
from .mapper import MonthInfoMapper, MonthInfoRewardSourceMapper
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
        month_info_mapper = self._convert_month_info(month_info)
        db.insert(month_info_mapper, "update")
        db.insert_batch(self._convert_reward_source(month_info), "update")

    def _convert_month_info(self, month_info: MonthInfo):
        """将 MonthInfo 转换为 MonthInfoMapper"""
        return MonthInfoMapper(
            uid=self.user.uid,
            month=month_info.data_month,
            hcoin=month_info.month_data.current_hcoin,
            rails_pass=month_info.month_data.current_rails_pass,
        )

    def _convert_reward_source(self, month_info: MonthInfo):
        return [
            MonthInfoRewardSourceMapper(
                uid=self.user.uid,
                month=month_info.data_month,
                action=item.action,
                num=item.num,
                percent=item.percent,
                action_name=item.action_name,
            )
            for item in month_info.month_data.group_by
        ]

    def query_month_info(self, length: int = 6):
        """查询最近 length 条数据
        # TODO 默认长度根据屏幕的显示效果确定
        """
        query_sql = """SELECT * FROM month_info WHERE uid = "{}" ORDER BY month DESC LIMIT {}
        """.format(
            self.user.uid, length
        )
        cursor = db.select(query_sql)
        res = cursor.fetchall()
        return convert(res, MonthInfoMapper)

    def _gen_month_info_tables(self, month_infos: typing.List[MonthInfoMapper]):
        month_info_table = PrettyTable()

        month_info_table.align = "l"
        month_info_table.title = "开拓月历"
        month_info_table.add_column(
            "日期",  # month
            ["星穹", "票数"],  # star_coin  # rails_pass
        )
        for item in month_infos:
            month_info_table.add_column(item.month, [item.hcoin, item.rails_pass])
        return month_info_table

    def visualization(self):
        functional.clear_screen()
        print("UID:", functional.color_str("{}".format(self.user.uid), "green"))
        month_info_data = self.query_month_info()
        print(self._gen_month_info_tables(month_info_data))

    def refresh_month_info(self):
        cur_month_data = self.fetch_month_info()
        datas = []
        datas.append(cur_month_data)
        for month in cur_month_data.optional_month[1:]:
            cur_month_data = self.fetch_month_info(month)
            datas.append(cur_month_data)
        for month_data in datas:
            self._save_or_update_month_info(month_data)
