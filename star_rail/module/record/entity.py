from __future__ import annotations

import typing

from star_rail.database import DbClient, DbField, DbModel
from star_rail.module.base import BaseClient
from star_rail.utils import Date

from .model import GachaRecordItem

if typing.TYPE_CHECKING:
    from .model import GachaRecordInfo


class GachaRecordBatchEntity(DbModel):
    __table_name__ = "gacha_record_batch"

    uid: str
    batch_id: int = DbField(primary_key=True)
    """抽卡记录的批次"""
    lang: str
    """当前记录批次的lang"""
    region_time_zone: int
    """跃迁记录时区"""
    source: str
    """抽卡记录来源

    [{APP_NAME} | {third_party_app_name} ]
    """
    count: int
    """本次插入或更新的抽卡记录数量"""
    timestamp: int
    """与 region_time_zone 同时区的时间戳"""


class GachaRecordItemEntity(DbModel):
    __table_name__ = "gacha_record_item"

    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str = DbField(primary_key=True)
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str
    batch_id: int


class GachaRecordDbClient(BaseClient):
    @staticmethod
    async def get_next_batch_id() -> int:
        """从批次表中获取下一个可用的批次ID"""
        sql = """select coalesce(max(batch_id), 0) + 1 as next_batch_id from gacha_record_batch;"""
        async with DbClient() as db:
            cursor = await db.execute(sql)
            row = await cursor.fetchone()
            return row[0]

    async def get_latest_batch(self) -> GachaRecordBatchEntity | None:
        sql = """select * from gacha_record_batch where uid = ? order by batch_id desc limit 1;"""
        async with DbClient() as db:
            cursor = await db.execute(sql, self.user.uid)
            row = await cursor.fetchone()
            return db.convert(row, GachaRecordBatchEntity)

    async def get_latest_gacha_record(self) -> GachaRecordItem | None:
        """根据UID查询出最近的一条记录"""
        sql = """select * from gacha_record_item where uid = ? order by id desc limit 1;"""
        async with DbClient() as db:
            cursor = await db.execute(sql, self.user.uid)
            row = await cursor.fetchone()
            record_item_entity = db.convert(row, GachaRecordItemEntity)

        if not record_item_entity:
            return None

        return _convert_to_record_item(record_item_entity)

    async def get_all_gacha_record(self) -> list[GachaRecordItem]:
        """查询所有抽卡记录"""
        sql = """select * from gacha_record_item where uid = ? order by id;"""
        async with DbClient() as db:
            cursor = await db.execute(sql, self.user.uid)
            rows = await cursor.fetchall()
            record_item_entity_list = db.convert_list(rows, GachaRecordItemEntity)

        return _convert_to_record_item(record_item_entity_list)

    async def insert_gacha_record(
        self,
        gacha_record_list: list[GachaRecordItem],
        info: GachaRecordInfo,
        mode: typing.Literal["ignore", "replace", "none"],
    ):
        """批量插入抽卡记录"""
        record_item_entity_list = _convert_to_record_item_entity(gacha_record_list, info.batch_id)

        async with DbClient() as db:
            await db.start_transaction()

            insert_cnt = await db.insert(record_item_entity_list, mode)
            if insert_cnt == 0:
                # 数据库无新增记录
                await db.commit_transaction()
                return insert_cnt

            record_batch_entity = GachaRecordBatchEntity(
                uid=info.uid,
                batch_id=info.batch_id,
                lang=info.lang,
                region_time_zone=info.region_time_zone,
                source=info.source,
                count=insert_cnt,
                timestamp=int(Date.local_time_to_timezone(info.region_time_zone).timestamp()),
            )
            await db.insert(record_batch_entity, "none")

            await db.commit_transaction()
        return insert_cnt

    async def get_all_batch_data(self):
        sql = """select * from gacha_record_batch where uid = ? order by batch_id desc;"""
        async with DbClient() as db:
            cursor = await db.execute(sql, self.user.uid)
            rows = await cursor.fetchall()
            return db.convert_list(rows, GachaRecordBatchEntity)

    async def delete_record_by_batch(self, batch_id: int):
        delete_record_sql = """delete from gacha_record_item where batch_id = ? and uid = ?;"""
        delete_batch_sql = """delete from gacha_record_batch where batch_id = ? and uid = ?;"""
        async with DbClient() as db:
            await db.start_transaction()
            await db.execute(delete_record_sql, batch_id, self.user.uid)
            await db.execute(delete_batch_sql, batch_id, self.user.uid)
            await db.commit_transaction()


def _convert_to_record_item_entity(
    data: GachaRecordItem | list[GachaRecordItem], batch_id: int
) -> list[GachaRecordItemEntity] | GachaRecordItemEntity:
    if isinstance(data, list):
        return [_convert_to_record_item_entity(item, batch_id) for item in data]
    elif isinstance(data, GachaRecordItem):
        return GachaRecordItemEntity(
            gacha_id=data.gacha_id,
            gacha_type=data.gacha_type,
            item_id=data.item_id,
            time=data.time,
            id=data.id,
            count=data.count,
            name=data.name,
            rank_type=data.rank_type,
            uid=data.uid,
            lang=data.lang,
            item_type=data.item_type,
            batch_id=batch_id,
        )
    else:
        raise AssertionError(
            "Param type error. Expected type 'list' or 'GachaRecordItemEntity',"
            f" got [{type(data)}]."
        )


def _convert_to_record_item(
    data: GachaRecordItemEntity | list[GachaRecordItemEntity],
) -> list[GachaRecordItem] | GachaRecordItem:
    if isinstance(data, list):
        return [_convert_to_record_item(item) for item in data]
    elif isinstance(data, GachaRecordItemEntity):
        return GachaRecordItem(
            gacha_id=data.gacha_id,
            gacha_type=data.gacha_type,
            item_id=data.item_id,
            time=data.time,
            id=data.id,
            count=data.count,
            name=data.name,
            rank_type=data.rank_type,
            uid=data.uid,
            lang=data.lang,
            item_type=data.item_type,
        )
    else:
        raise AssertionError(
            "Param type error. Expected type 'list' or 'GachaRecordItemEntity',"
            f" got [{ type(data)}]."
        )
