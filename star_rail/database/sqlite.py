from __future__ import annotations

import os
import sqlite3
import typing
from collections import deque

import aiosqlite
import pydantic
from loguru import logger

from star_rail import constants
from star_rail.utils import Date

from .upgrade_sql import DB_VERSION, UpgradeSQL

__all__ = ["DbModel", "DbField", "DbClient", "DB_VERSION"]


class DbModel(pydantic.BaseModel):
    __subclass_table__: list = []

    __table_name__: str

    @staticmethod
    def _register(subclass):
        DbModel.__subclass_table__.append(subclass)

    def __init_subclass__(cls):
        cls._register(cls)


def DbField(primary_key=False, **kwargs):
    extra = {"primary_key": primary_key}
    return pydantic.Field(json_schema_extra=extra, **kwargs)


_T = typing.TypeVar("_T", bound=DbModel)


class DbModelInfo(pydantic.BaseModel):
    table_name: str
    column: set[str] = set()
    primary_key: set[str] = set()

    @classmethod
    def parse(cls, model_cls: type[_T]):
        table_name = getattr(model_cls, "__table_name__", None)

        if table_name is None:
            raise AssertionError(
                f"Undefined `__table_name__` attribute in [{model_cls.__class__.__name__}]"
            )

        model_info = cls(table_name=table_name)

        for name, fields in model_cls.model_fields.items():
            if fields.json_schema_extra and fields.json_schema_extra.get("primary_key", None):
                model_info.primary_key.add(name)
            model_info.column.add(name)

        return model_info


class DbClient:
    DB_PATH: str = os.path.join(constants.DATA_PATH, "star_rail.db")
    connection: aiosqlite.Connection | None
    sql_queue: deque

    def __init__(self) -> None:
        self.connection: aiosqlite.Connection | None = None
        self.sql_queue = deque(maxlen=20)

    async def connect(self):
        self.connection = await aiosqlite.connect(self.DB_PATH, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        await self.connection.set_trace_callback(self.sql_queue.append)

    async def start_transaction(self):
        await self.connection.execute("BEGIN")

    async def commit_transaction(self):
        await self.connection.commit()

    async def rollback_transaction(self):
        await self.connection.rollback()

    async def close(self):
        await self.connection.close()

        self.connection = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.connection.in_transaction:
            if exc_type is None:
                await self.commit_transaction()
            else:
                await self.rollback_transaction()
                logger.debug("[SQL traceback]:\n{}", "\n".join(self.sql_queue))

        await self.close()

    async def execute(self, sql: str, *params):
        params = tuple(params)
        return await self.connection.execute(sql, params)

    if typing.TYPE_CHECKING:

        @typing.overload
        async def insert(
            self, item: DbModel, mode: typing.Literal["ignore", "replace", "none"] = "none"
        ) -> int:
            pass

        @typing.overload
        async def insert(
            self, items: list[DbModel], mode: typing.Literal["ignore", "replace", "none"] = "none"
        ) -> int:
            pass

    async def insert(
        self,
        item_or_item_list: DbModel | list[DbModel],
        mode: typing.Literal["ignore", "replace", "none"] = "none",
    ) -> int:
        if mode == "none":
            mode = ""
        elif mode == "ignore":
            mode = " or ignore "
        elif mode == "replace":
            mode = " or replace "
        else:
            raise AssertionError(
                f"Param error. Expected 'ignore', 'replace' or 'none', got [{mode}]"
            )

        if isinstance(item_or_item_list, list):
            item_list = item_or_item_list
            if not item_list:
                return 0

            cls_info = DbModelInfo.parse(type(item_list[0]))
            columns = ",".join(cls_info.column)
            placeholders = ",".join(["?" for _ in cls_info.column])
            values = []
            for item in item_list:
                item_values = [getattr(item, k) for k in cls_info.column]
                values.append(item_values)
            sql_statement = (
                f"""insert {mode} into {cls_info.table_name} ({columns}) values ({placeholders});"""
            )
            cursor = await self.connection.executemany(sql_statement, values)
        elif isinstance(item_or_item_list, DbModel):
            item = item_or_item_list
            cls_anno = DbModelInfo.parse(type(item))
            columns = ",".join(cls_anno.column)
            placeholders = ",".join(["?" for _ in cls_anno.column])
            values = [getattr(item, k) for k in cls_anno.column]

            sql_statement = (
                f"""insert {mode} into {cls_anno.table_name} ({columns}) values ({placeholders});"""
            )
            cursor = await self.connection.execute(sql_statement, values)
        else:
            raise AssertionError(
                "Param type error. Expected type 'list' or 'DBModel',"
                f"got [{type(item_or_item_list)}]"
            )

        return cursor.rowcount

    def convert(self, row: sqlite3.Row | None, model_cls: type[_T]) -> _T | None:
        if row is None:
            return None
        data = {k: row[k] for k in row.keys()}
        return model_cls(**data)

    def convert_list(self, rows: list[sqlite3.Row], model_cls: type[_T]) -> list[_T]:
        return [model_cls(**{k: row[k] for k in row.keys()}) for row in rows]

    async def create_all_table(self):
        logger.debug("Create all table")
        await self.start_transaction()
        for model_cls in DbModel.__subclass_table__:
            model_anno = DbModelInfo.parse(model_cls)

            sql = """create table if not exists {} ({}, primary key ({}) );""".format(
                model_anno.table_name,
                ",".join(model_anno.column),
                ",".join(model_anno.primary_key),
            )
            await self.execute(sql)
        await self.commit_transaction()

    async def get_user_version(self):
        logger.debug("Get database version")
        cursor = await self.connection.execute("pragma user_version;")
        row = await cursor.fetchone()
        return row[0]

    async def set_user_version(self, db_version: int):
        logger.debug("Set database version to {}", db_version)
        await self.connection.execute(f"pragma user_version = {db_version};")

    def upgrade_manager(self):
        return UpgradeManager(self)


class UpgradeManager:
    def __init__(self, db_client: DbClient) -> None:
        self.db_client = db_client
        self.backup_dir = constants.DATA_PATH

    async def upgrade_database(self):
        logger.debug("Update database version")
        local_db_version = await self.db_client.get_user_version()
        if local_db_version >= DB_VERSION:
            return

        upgrade_script_list = sorted(UpgradeSQL.register, key=lambda x: x.target_version)
        for upgrade_script in upgrade_script_list:
            if local_db_version < upgrade_script.target_version <= DB_VERSION:
                await self._migrate(upgrade_script)
                local_db_version = await self.db_client.get_user_version()
                logger.debug("current database version: {}", local_db_version)
        await self.db_client.execute("VACUUM;")

    async def _migrate(self, migration_sql: UpgradeSQL):
        logger.debug("Upgrade database version to {}", migration_sql.target_version)
        await self.db_client.start_transaction()
        for sql in migration_sql.sql_list:
            await self.db_client.execute(sql)
        await self.db_client.execute(f"pragma user_version = {migration_sql.target_version};")
        await self.db_client.commit_transaction()
        logger.debug("Upgrade database version to {} completed", migration_sql.target_version)

    # TODO 测试
    async def backup_database(self):
        logger.debug("Backup database")

        backup_file = os.path.join(
            self.backup_dir,
            f"star_rail_backup_{Date.now().strftime(Date.Format.YYYYMMDDHHMMSS)}.db",
        )
        async with aiosqlite.connect(backup_file) as backup_conn:
            await self.db_client.connection.backup(backup_conn)
        logger.debug("Backup database completed")
