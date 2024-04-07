from __future__ import annotations

import typing

from star_rail.utils.date import Date
from star_rail.utils.logger import logger

from ..base import BaseClient
from .mapper import GachaRecordBatchMapper, GachaRecordItemMapper

if typing.TYPE_CHECKING:
    from .model import GachaRecordItem, GachaRecordArchiveInfo

from star_rail.database import AsyncDBClient


class GachaRecordRepository(BaseClient):
    async def get_next_batch_id(self) -> int:
        """从批次表中获取下一个可用的批次ID"""
        return await GachaRecordBatchMapper.query_next_batch_id()

    async def get_all_batch(self):
        """查询所有批次信息"""

    async def get_latest_batch(self) -> GachaRecordBatchMapper | None:
        return await GachaRecordBatchMapper.query_latest_batch(self.user.uid)

    async def get_latest_gacha_record_by_uid(self) -> typing.Optional[GachaRecordItem]:
        """根据UID查询出最近的一条记录"""
        record_mapper = await GachaRecordItemMapper.query_latest_gacha_record(self.user.uid)
        if not record_mapper:
            return None
        from . import converter

        return converter.convert_to_record_item(record_mapper)

    async def get_all_gacha_record(self) -> list[GachaRecordItem]:
        """查询账号的所有抽卡记录"""
        record_mapper_list = await GachaRecordItemMapper.query_all_gacha_record(self.user.uid)
        from . import converter

        return converter.convert_to_record_item(record_mapper_list)

    async def insert_gacha_record(
        self, gacha_record_list: list[GachaRecordItem], info: GachaRecordArchiveInfo
    ):
        """批量插入抽卡记录

        Args:
            gacha_record_list (list[GachaRecordItem]): 抽卡记录
            info (GachaRecordArchiveInfo): 抽卡记录归档信息
        """
        logger.debug("Insert gacha record data.")
        from . import converter

        record_item_mapper_list = converter.convert_to_record_item_mapper(
            gacha_record_list, info.batch_id
        )

        async with AsyncDBClient() as db:
            await db.start_transaction()
            cnt = await db.insert(record_item_mapper_list, mode="ignore")

            if cnt == 0:
                # 数据库无新增记录
                return 0

            record_batch_mapper = GachaRecordBatchMapper(
                uid=info.uid,
                batch_id=info.batch_id,
                lang=info.lang,
                region_time_zone=info.region_time_zone,
                source=info.source,
                count=cnt,
                timestamp=int(Date.convert_timezone(info.region_time_zone).timestamp()),
            )
            await db.insert(record_batch_mapper, "ignore")

            await db.commit_transaction()
        logger.debug("Add {} new gacha records.", cnt)
        return cnt
