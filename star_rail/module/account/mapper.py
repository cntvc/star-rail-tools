import typing

from star_rail.database import AsyncDBClient, DBField, DBModel


class AccountMapper(DBModel):
    __table_name__ = "user"

    uid: str = DBField(primary_key=True)

    cookie: str

    region: str

    game_biz: str

    @staticmethod
    async def query_by_uid(uid: str) -> typing.Optional["AccountMapper"]:
        sql = """select * from user where uid = ?;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql, uid)
            return db.convert(await cursor.fetchone(), AccountMapper)

    @staticmethod
    async def query_all_uid() -> list[str]:
        sql = """select uid from user order by uid;"""
        async with AsyncDBClient() as db:
            cursor = await db.execute(sql)
            return [r[0] for r in await cursor.fetchall()]

    @staticmethod
    async def add_account(account_mapper: "AccountMapper") -> int:
        async with AsyncDBClient() as db:
            return await db.insert(account_mapper, mode="update")

    @staticmethod
    async def delete_account(uid: str):
        async with AsyncDBClient() as db:
            sql = """delete from user where uid = ?;"""
            cursor = await db.execute(sql, uid)
            return cursor.rowcount
