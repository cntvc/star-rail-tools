import typing

from star_rail import exceptions as error
from star_rail.module import routes
from star_rail.module.base import BaseClient
from star_rail.utils.logger import logger

from ..web import request
from .mapper import MonthInfoItemMapper
from .model import MonthInfoData, MonthInfoItem

__all__ = ["MonthInfoClient"]

from star_rail.utils.date import Date


class MonthInfoClient(BaseClient):
    async def _fetch_month_info(self, month: str = "") -> MonthInfoData:
        """获取指定月份的月历数据

        Args:
            month (str): 格式 'YYYYMM', 默认 '' 时查询当前月份

        Returns:
            MonthInfoData: 月历数据
        """
        param = {"uid": self.user.uid, "region": self.user.region, "month": month}

        data = await request(
            method="GET",
            url=routes.MONTH_INFO_URL.get_url(self.user.game_biz),
            params=param,
            cookies=self.user.cookie.model_dump("all"),
        )
        return MonthInfoData(**data)

    async def get_month_info_history(self, month_nums: int | None = None) -> list[MonthInfoItem]:
        """查询最近 month_nums 条月历信息的历史数据

        Args:
            month_nums (int, optional): 查询最近数据的数量，为空查询全部数据.

        Returns:
            list[MonthInfoItemMapper]: 按时间倒序的月历数据
        """
        mapper_list = await MonthInfoItemMapper.query_by_range(self.user.uid, month_nums)
        from . import converter

        return converter.convert_to_month_info_item(mapper_list)

    async def get_month_info_by_month(self, month: str) -> typing.Optional[MonthInfoItemMapper]:
        """查询指定月份的月历信息

        Args:
            month (str): 格式 'YYYYMM'

        Returns:
            typing.Optional[MonthInfoItemMapper]: 月历数据
        """
        return await MonthInfoItemMapper.query_by_month(self.user.uid, month)

    async def _save_month_info(self, month_info_data: list[MonthInfoData]) -> int:
        """保存月历信息

        Args:
            month_info_data (list[MonthInfoData]): 月历数据

        Returns:
            int: 成功更新的条目数量
        """
        from . import converter

        update_time = Date.format_time()
        month_mapper_list = converter.convert_to_month_info_mapper(month_info_data, update_time)
        return await MonthInfoItemMapper.save_month_info(month_mapper_list)

    async def refresh_month_info(self) -> int:
        """刷新最近3个月开拓月历数据

        Returns:
            int: 成功更新的月份数量
        """
        logger.debug("Refresh month info.")
        if self.user.cookie.empty_cookie_token():
            raise error.InvalidCookieError()
        try:
            cur_month_info_data = await self._fetch_month_info()
        except error.InvalidCookieError:
            # cookie_token 有效期比stoken短，因此尝试刷新一次
            logger.debug("The cookie_token value has expired.")
            await self.user.cookie.refresh_cookie_token(self.user.game_biz)
            await self.user.save_profile()
            cur_month_info_data = await self._fetch_month_info()

        datas = [cur_month_info_data]
        for month in cur_month_info_data.optional_month[1:]:
            cur_month_info_data = await self._fetch_month_info(month)
            datas.append(cur_month_info_data)
        return await self._save_month_info(datas)
