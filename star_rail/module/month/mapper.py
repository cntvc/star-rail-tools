import typing

from star_rail.database import AsyncDBClient, DBField, DBModel


class MonthInfoItemMapper(DBModel):
    __table_name__ = "month_info_item"

    uid: str = DBField(primary_key=True)
    """用户id"""

    month: str = DBField(primary_key=True)
    """月份"""

    hcoin: int
    """星穹"""

    rails_pass: int
    """列车票"""

    source: str
    """开拓月历星穹来源"""

    update_time: str

    @staticmethod
    async def query_by_month(uid: str, month: str) -> typing.Optional["MonthInfoItemMapper"]:
        sql = """select * from month_info_item where month = ? and uid = ?;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, month, uid)
            row = await cursor.fetchone()
            return db.convert(row, MonthInfoItemMapper)

    @staticmethod
    async def query_by_range(uid: str, _range: int) -> list["MonthInfoItemMapper"]:
        sql = """select * from month_info_item where uid = ? order by month desc limit ?;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, uid, _range)
            row = await cursor.fetchall()
            return db.convert(row, MonthInfoItemMapper)

    @staticmethod
    async def save_month_info(data_list: list["MonthInfoItemMapper"]) -> int:
        async with AsyncDBClient() as db:
            return await db.insert(data_list, mode="update")
