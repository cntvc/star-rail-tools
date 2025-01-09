from __future__ import annotations

import functools
import typing

import yarl

from star_rail import exceptions
from star_rail.module.types import GameBiz
from star_rail.network import CursorPaginator, MergedPaginator, Paginator, request

from .model import GachaRecordItem, GachaRecordPage
from .types import GACHA_TYPE_IDS

_GACHA_RECORD_CN_URL = yarl.URL(
    "https://public-operation-hkrpg.mihoyo.com/common/gacha_record/api/getGachaLog"
)
_GACHA_RECORD_OS_URL = yarl.URL(
    "https://public-operation-hkrpg-sg.hoyoverse.com/common/gacha_record/api/getGachaLog"
)


__all__ = ["GachaRecordFetcher"]


class GachaRecordFetcher:
    def __init__(self, url: yarl.URL) -> None:
        self.url = self._build_url(url)

    def _build_url(self, url: yarl.URL):
        """过滤并替换URL的请求路径，只保留必要的参数"""
        required_params = ("authkey", "lang", "game_biz", "authkey_ver")
        filtered_params = {key: value for key, value in url.query.items() if key in required_params}
        if len(filtered_params) != len(required_params):
            raise exceptions.GachaRecordError("链接缺少必要参数")
        gacha_url = _GACHA_RECORD_CN_URL
        if filtered_params["game_biz"] == GameBiz.GLOBAL.value:
            gacha_url = _GACHA_RECORD_OS_URL
        return gacha_url.with_query(filtered_params)

    async def get_url_info(self):
        """获取URL对应的 UID、lang和region"""
        uid, lang, region_time_zone = "", "", ""
        for gacha_type in GACHA_TYPE_IDS:
            data = await self._fetch_gacha_record_page(gacha_type, 1, 0)
            if data.list:
                region_time_zone = data.region_time_zone
                uid = data.list[0].uid
                lang = data.list[0].lang
                break
        return uid, lang, region_time_zone

    async def _fetch_gacha_record_page(
        self, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> GachaRecordPage:
        query_params = {
            "size": size,
            "gacha_type": gacha_type,
            "end_id": end_id,
        }
        query_params.update(self.url.query)
        return GachaRecordPage(**await request("GET", url=self.url, params=query_params))

    async def _fetch_gacha_record(
        self, gacha_type: int | str, size: int | str, end_id: int | str
    ) -> typing.Sequence[GachaRecordItem]:
        gacha_data = await self._fetch_gacha_record_page(gacha_type, size, end_id)
        return gacha_data.list

    async def fetch_gacha_record(
        self,
        *,
        gacha_type_list: str | typing.Sequence[str] | None = None,
        stop_id: str | None = None,
    ) -> Paginator[GachaRecordItem]:
        """获取跃迁记录

        Args:
            gacha_type_list: 需要查询的卡池id列表. 默认为 None 时查询全部卡池.
            stop_id: 停止查询的ID. 默认为 None 时查询全部记录

        Returns:
            Paginator[GachaRecordItem]: 按ID从大到小排列的跃迁记录迭代器
        """
        gacha_type_list = gacha_type_list or GACHA_TYPE_IDS

        if not isinstance(gacha_type_list, typing.Sequence):
            gacha_type_list = [gacha_type_list]

        max_page_size = 20
        iterators: list[Paginator[GachaRecordItem]] = []

        for gacha_type in gacha_type_list:
            iterators.append(
                CursorPaginator(
                    functools.partial(
                        self._fetch_gacha_record,
                        gacha_type=gacha_type,
                        size=max_page_size,
                    ),
                    stop_id=stop_id,
                )
            )

        if len(iterators) == 1:
            return iterators[0]

        # 合并迭代器时使用小顶堆排序，每个迭代器数据按ID从大到小排列
        # 使用 `-int(x.id)` 比较，确保按ID从大到小排序
        return MergedPaginator(iterators, key=lambda x: -int(x.id))
