import typing

from star_rail.database import AsyncDBClient, DBField, DBModel


class GachaRecordBatchMapper(DBModel):
    __table_name__ = "gacha_record_batch"

    uid: str
    batch_id: int = DBField(primary_key=True)
    """抽卡记录的批次"""
    lang: str
    """当前记录批次的lang"""
    region_time_zone: int
    """服务器时区"""
    source: str
    """抽卡记录来源

        "[URL]" : 剪切板或游戏web缓存获取的链接\n
        "[{app_name}]" : 从其他app导入的SRGF数据
    """
    count: int
    """本次插入或更新的抽卡记录数量"""
    timestamp: int
    """与 region_time_zone 同时区的时间戳"""

    @staticmethod
    async def query_next_batch_id() -> int:
        sql = """select coalesce(max(batch_id), 0) + 1 as next_batch_id from gacha_record_batch;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql)
            row = await cursor.fetchone()
            return row[0]

    @staticmethod
    async def query_latest_batch(uid: str) -> typing.Optional["GachaRecordBatchMapper"]:
        """查询最近的一次插入信息"""
        sql = """select * from gacha_record_batch where uid = ? order by batch_id desc limit 1;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, (uid,))
            row = await cursor.fetchone()
            return db.convert(row, GachaRecordBatchMapper)


class GachaRecordItemMapper(DBModel):
    __table_name__ = "gacha_record_item"

    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str = DBField(primary_key=True)
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str
    batch_id: int
    """批次id"""

    @staticmethod
    async def query_latest_gacha_record(uid: str) -> typing.Optional["GachaRecordItemMapper"]:
        sql = """select * from gacha_record_item where uid = ? order by id desc limit 1;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, (uid,))
            row = await cursor.fetchone()
            return db.convert(row, GachaRecordItemMapper)

    @staticmethod
    async def query_all_gacha_record(uid: str) -> list["GachaRecordItemMapper"]:
        sql = """select * from gacha_record_item where uid = ? order by id;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, (uid,))
            row = await cursor.fetchall()
            return db.convert(row, GachaRecordItemMapper)
