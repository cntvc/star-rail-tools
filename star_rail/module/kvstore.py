from star_rail.database import DbClient, DbField, DbModel


class KVStoreEntity(DbModel):
    __table_name__ = "kvstore"
    key: str = DbField(primary_key=True)
    value: str


class KVStore:
    cache = {}

    @staticmethod
    async def get(key: str) -> str | None:
        if key in KVStore.cache:
            return KVStore.cache[key]

        sql = "SELECT * FROM kvstore WHERE key=?"
        async with DbClient() as db:
            cursor = await db.execute(sql, key)
            kv = db.convert(await cursor.fetchone(), KVStoreEntity)
            if kv is None:
                return None
            return kv.value

    @staticmethod
    async def set(key: str, value: str, force: bool = False) -> None:
        if force:
            async with DbClient() as db:
                await db.insert(KVStoreEntity(key=key, value=value), "replace")
                KVStore.cache[key] = value
                return

        if key not in KVStore.cache:
            async with DbClient() as db:
                await db.insert(KVStoreEntity(key=key, value=value), "replace")
            KVStore.cache[key] = value
        elif KVStore.cache[key] != value:
            sql = """UPDATE kvstore SET value=? WHERE key=?;"""
            async with DbClient() as db:
                await db.execute(sql, value, key)
            KVStore.cache[key] = value
        else:
            return
