import time

from rich import box
from rich.console import Console
from rich.style import Style
from rich.table import Table

from star_rail import exceptions as error
from star_rail.database import DataBaseClient
from star_rail.i18n import i18n
from star_rail.module import Account, routes
from star_rail.module.api_helper import request
from star_rail.utils import functional
from star_rail.utils.log import logger

from . import converter as converter
from .mapper import MonthInfoMapper, MonthInfoRecordMapper
from .model import MonthInfo, MonthInfoData

__all__ = ["MonthClient"]


class MonthClient:
    def __init__(self, user: Account) -> None:
        self.user = user

    def fetch_month_info(self, month: str = ""):
        """获取开拓月历"""

        param = {"uid": self.user.uid, "region": self.user.region, "month": month}

        data = request(
            method="get",
            url=routes.MONTH_INFO_URL.get_url(),
            params=param,
            cookies=self.user.cookie.model_dump("all"),
        )
        return MonthInfoData(**data)

    def _save_or_update_month_info(self, month_info_data: MonthInfoData):
        month_info_mapper = converter.month_info_data_to_month_info_mapper(
            self.user, month_info_data
        )
        reward_source_mapper_list = converter.month_info_data_to_reward_source_mapper(
            self.user, month_info_data
        )
        with DataBaseClient() as db:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            db.insert(MonthInfoRecordMapper(uid=self.user.uid, update_time=current_time), "update")
            db.insert(month_info_mapper, "update")
            db.insert_batch(reward_source_mapper_list, "update")

    def _create_month_info_tables(self, month_info_list: list[MonthInfo]):
        table = Table(
            title=i18n.table.trailblaze_calendar.title,
            box=box.ASCII2,
            title_style=Style(color="cadet_blue", bold=True),
        )

        table.add_column(
            i18n.table.trailblaze_calendar.month, header_style=Style(color="cadet_blue")
        )
        for info in month_info_list:
            table.add_column(info.month, header_style=Style(color="cadet_blue"))
        table.add_row(
            i18n.table.trailblaze_calendar.hcoin, *[str(info.hcoin) for info in month_info_list]
        )
        table.add_row(
            i18n.table.trailblaze_calendar.rails_pass,
            *[str(info.rails_pass) for info in month_info_list]
        )
        return table

    def show_month_info(self):
        data = []
        month_info_record = MonthInfoRecordMapper.query(self.user.uid)
        if month_info_record:
            month_info_mappers = MonthInfoMapper.query(self.user.uid, None, 6)

            if month_info_mappers:
                data = converter.mapper_to_month_info(month_info_mappers)
        functional.clear_all()
        print("UID:", functional.color_str("{}".format(self.user.uid), "green"))
        print(
            i18n.month.client.update_time,
            month_info_record.update_time if month_info_record else "",
            end="\n\n",
        )
        Console().print(self._create_month_info_tables(data))

    def refresh_month_info(self):
        """刷新最近3个月的开拓月历数据"""
        logger.debug("refresh month info")
        try:
            current_month_info_data = self.fetch_month_info()
        except error.InvalidCookieError:
            # Cookie token 无效时，主动刷新一次，如果仍然无效，表示 Stoken 失效或者被风控
            self.user.cookie.refresh_cookie_token()
            self.user.save_profile()
            current_month_info_data = self.fetch_month_info()

        datas = [current_month_info_data]
        for month in current_month_info_data.optional_month[1:]:
            current_month_info_data = self.fetch_month_info(month)
            datas.append(current_month_info_data)
        for month_data in datas:
            self._save_or_update_month_info(month_data)
