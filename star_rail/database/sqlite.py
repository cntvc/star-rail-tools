"""异步 SQLite 客户端封装"""

import os
import sqlite3
import typing
from collections import deque
from typing import Optional

import aiosqlite
import pydantic

from star_rail import constants
from star_rail.utils.logger import logger

from .upgrade_sql import DATABASE_VERSION, UpgradeSQL

_DEFAULT_DB_PATH = os.path.join(constants.DATA_PATH, "star_rail.db")

__all__ = ["DBModel", "DBField", "AsyncDBClient", "DBManager"]


class DBModel(pydantic.BaseModel):
    """数据库模型基类

    继承自 pydantic.BaseModel ，只用于 Sqlite ，以成员定义时的类型声明限制数据类型
    """

    __subclass_table__: list = []
    """子类注册表"""

    __table_name__: str
    """数据库表名"""

    @staticmethod
    def _register(subclass):
        DBModel.__subclass_table__.append(subclass)

    def __init_subclass__(cls):
        cls._register(cls)


def DBField(primary_key=False, **kwargs):
    """数据库模型参数扩展"""
    extra = {"primary_key": primary_key}
    return pydantic.Field(json_schema_extra=extra, **kwargs)


_T = typing.TypeVar("_T", bound=DBModel)


class ModelInfo(pydantic.BaseModel):
    table_name: str
    column: set[str] = set()
    primary_key: set[str] = set()

    @classmethod
    def parse(cls, model_cls: type[_T]):
        table_name = getattr(model_cls, "__table_name__", None)

        if table_name is None:
            raise AssertionError(
                "DataBase model error. Model name variable not found, "
                f"cls [{model_cls.__class__.__name__}]"
            )

        model_info = ModelInfo(table_name=table_name)

        for name, fields in model_cls.model_fields.items():
            if fields.json_schema_extra and fields.json_schema_extra.get("primary_key", None):
                model_info.primary_key.add(name)
            model_info.column.add(name)

        return model_info


class AsyncDBClient:
    db_path: str
    connection: aiosqlite.Connection
    sql_queue: deque
    """记录调用的SQL语句"""

    def __init__(self, *, db_path=_DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self.connection = None
        self._isolation_level = None
        self.sql_queue = deque(maxlen=20)

    async def connect(self):
        self.connection = await aiosqlite.connect(
            self.db_path, isolation_level=self._isolation_level
        )
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

    @typing.overload
    async def insert(
        self, item: DBModel, mode: typing.Literal["ignore", "update", "none"] = "none"
    ) -> int:
        pass

    @typing.overload
    async def insert(
        self, items: list[DBModel], mode: typing.Literal["ignore", "update", "none"] = "none"
    ) -> int:
        pass

    async def insert(
        self,
        item_or_item_list: DBModel | list[DBModel],
        mode: typing.Literal["ignore", "update", "none"] = "none",
    ) -> int:
        if mode == "none":
            mode = ""
        elif mode == "ignore":
            mode = " or ignore "
        elif mode == "update":
            mode = " or replace "
        else:
            raise AssertionError(
                f"Param error. Expected 'ignore', 'update' or 'none', got [{mode}]"
            )

        if isinstance(item_or_item_list, list):
            item_list = item_or_item_list
            if not item_list:
                return 0

            cls_info = ModelInfo.parse(type(item_list[0]))
            columns = ",".join(cls_info.column)
            placeholders = ",".join(["?" for _ in cls_info.column])
            values = []
            for item in item_list:
                item_values = [getattr(item, k) for k in cls_info.column]
                values.append(item_values)
            sql_statement = """ insert {} into {} ({}) values ({}) ;""".format(
                mode, cls_info.table_name, columns, placeholders
            )
            cursor = await self.connection.executemany(sql_statement, values)
        elif isinstance(item_or_item_list, DBModel):
            item = item_or_item_list
            cls_anno = ModelInfo.parse(type(item))
            columns = ",".join(cls_anno.column)
            placeholders = ",".join(["?" for _ in cls_anno.column])
            values = [getattr(item, k) for k in cls_anno.column]

            sql_statement = """insert {} into {} ({}) values ({}) ;""".format(
                mode, cls_anno.table_name, columns, placeholders
            )
            cursor = await self.connection.execute(sql_statement, values)
        else:
            raise AssertionError(
                "Param type error. Expected type 'list' or 'DBModel',"
                f"got [{type(item_or_item_list)}]."
            )

        return cursor.rowcount

    @typing.overload
    def convert(self, row: Optional[sqlite3.Row], model_cls: type[_T]) -> Optional[_T]:
        pass

    @typing.overload
    def convert(self, row: list[sqlite3.Row], model_cls: type[_T]) -> list[_T]:
        pass

    def convert(
        self, row: Optional[sqlite3.Row] | list[sqlite3.Row], model_cls: type[_T]
    ) -> _T | list[_T] | None:
        if row is None:
            return None
        if isinstance(row, sqlite3.Row):
            data = {k: row[k] for k in row.keys()}
            return model_cls(**data)
        elif isinstance(row, list):
            data = []
            for item in row:
                t = model_cls(**{k: item[k] for k in item.keys()})
                data.append(t)
            return data
        else:
            raise AssertionError(
                f"Param type error. Expected type 'list' or 'DBModel', got [{type(row)}]."
            )


class DBManager:
    def __init__(self, *, db_path=_DEFAULT_DB_PATH) -> None:
        self.db_path = db_path

    async def create_all(self):
        """创建所有表"""
        async with AsyncDBClient(db_path=self.db_path) as db:
            await db.start_transaction()
            for model_cls in DBModel.__subclass_table__:
                model_anno = ModelInfo.parse(model_cls)

                sql = """create table if not exists {} ({}, primary key ({}) );""".format(
                    model_anno.table_name,
                    ",".join(model_anno.column),
                    ",".join(model_anno.primary_key),
                )
                await db.execute(sql)
            await db.commit_transaction()

    async def user_version(self):
        """获取用户数据库版本"""
        async with AsyncDBClient(db_path=self.db_path) as db:
            cursor = await db.execute("pragma user_version;")
            row = await cursor.fetchone()
            return row[0]

    async def set_user_version(self, db_version: str):
        async with AsyncDBClient(db_path=self.db_path) as db:
            await db.execute(f"pragma user_version = {db_version};")

    async def upgrade_database(self):
        """升级数据库版本"""
        logger.debug("Update database version.")
        local_db_version = await self.user_version()
        if local_db_version >= DATABASE_VERSION:
            return

        upgrade_script_list = sorted(UpgradeSQL._register, key=lambda x: x.target_version)
        for upgrade_script in upgrade_script_list:
            if local_db_version < upgrade_script.target_version <= DATABASE_VERSION:
                await self._perform_upgrade_script(upgrade_script)
                local_db_version = await self.user_version()

                logger.debug("current database version: {}", local_db_version)

    async def _perform_upgrade_script(self, script: "UpgradeSQL"):
        logger.debug("Upgrade database version to {}", script.target_version)
        async with AsyncDBClient(db_path=self.db_path) as db:
            await db.start_transaction()
            for sql in script.sql_list:
                await db.execute(sql)
            await db.execute(f"pragma user_version = {script.target_version};")
            await db.commit_transaction()
            logger.debug("Upgrade database version to {} completed.", script.target_version)
