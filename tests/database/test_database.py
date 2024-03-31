import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import aiosqlite

from star_rail import exceptions as error
from star_rail.database.sqlite import (
    AsyncDBClient,
    DBField,
    DBManager,
    DBModel,
    ModelInfo,
    UpgradeSQL,
)


class TestModelAnnotation(unittest.TestCase):
    def setUp(self) -> None:
        # 清空全局注册表
        DBModel.__subclass_table__ = []

    def test_parse(self):
        class TestModel(DBModel):
            __table_name__ = "test_table"
            name: str = DBField(primary_key=True)
            age: int

        annotation = ModelInfo.parse(TestModel)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.table_name, "test_table")
        self.assertSetEqual(annotation.column, {"name", "age"})
        self.assertSetEqual(annotation.primary_key, {"name"})

    def test_parse_without_table_name(self):
        class TestModel(DBModel):
            name: str
            age: int

        self.assertRaises(error.DataBaseError, ModelInfo.parse, TestModel)


class TestAsyncClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # 清空全局注册表
        DBModel.__subclass_table__ = []
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.client = AsyncDBClient(db_path=self.db_path)

    async def asyncTearDown(self):
        if self.client.connection is not None:
            await self.client.close()
        shutil.rmtree(self.tmp_dir)

    async def test_transaction(self):
        await self.client.connect()
        self.assertIsNotNone(self.client.connection)
        await self.client.start_transaction()
        self.assertTrue(self.client.connection.in_transaction)
        await self.client.commit_transaction()
        self.assertFalse(self.client.connection.in_transaction)

    @patch("aiosqlite.connect", new_callable=AsyncMock, side_effect=aiosqlite.Error)
    async def test_async_with_db_error(self, mock_connect):
        # 进入with语句块时出现异常（连接异常
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection

        with self.assertRaises(error.DataBaseError):
            async with self.client:
                pass

    @patch("aiosqlite.connect", new_callable=AsyncMock)
    async def test_async_with_aiosqlit_error_no_transaction(self, mock_connect):
        # with语句块内部出现异常，无事务
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection

        with self.assertRaises(aiosqlite.Error):
            async with self.client:
                mock_connection.in_transaction = False
                raise aiosqlite.OperationalError
        mock_connection.rollback.assert_not_called()
        mock_connection.close.assert_called_once()

    @patch("aiosqlite.connect", new_callable=AsyncMock)
    async def test_async_with_aiosqlit_error_in_transaction(self, mock_connect):
        # with语句块内部出现异常，且处于事务中
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        with self.assertRaises(aiosqlite.Error):
            async with self.client:
                mock_connection.in_transaction = True
                raise aiosqlite.OperationalError
        mock_connection.rollback.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("aiosqlite.connect", new_callable=AsyncMock)
    async def test_async_with_success_in_transaction(self, mock_connect):
        # with语句块无异常，且处于事务中
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        async with self.client:
            mock_connection.in_transaction = True
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("aiosqlite.connect", new_callable=AsyncMock)
    async def test_async_with_success_no_transaction(self, mock_connect):
        # with语句块无异常，无事务
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        async with self.client:
            mock_connection.in_transaction = False
        mock_connection.commit.assert_not_called()
        mock_connection.close.assert_called_once()

    async def test_execute(self):
        statements = []
        await self.client.connect()
        await self.client.connection.set_trace_callback(statements.append)
        await self.client.execute("create table if not exists user (id, name);")
        self.assertEqual(statements, ["create table if not exists user (id, name);"])

    async def test_insert(self):
        class UserModel(DBModel):
            __table_name__ = "user"
            id: str = DBField(primary_key=True)
            name: str

        await self.client.connect()
        await self.client.execute("create table if not exists user (id, name, primary key (id) );")

        user_list = [
            UserModel(id="1", name="user1"),
            UserModel(id="2", name="user2"),
            UserModel(id="3", name="user3"),
            UserModel(id="4", name="user4"),
        ]
        cnt = await self.client.insert(user_list[0], "ignore")
        self.assertEqual(cnt, 1)

        cnt = await self.client.insert([], "ignore")
        self.assertEqual(cnt, 0)

        cnt = await self.client.insert(user_list, "ignore")
        self.assertEqual(cnt, 3)

        cnt = await self.client.insert(UserModel(id="1", name="user1_new"), "update")
        self.assertEqual(cnt, 1)

    async def test_convert(self):
        class UserModel(DBModel):
            __table_name__ = "user"
            id: str = DBField(primary_key=True)
            name: str

        await self.client.connect()
        await self.client.execute("create table if not exists user (id, name, primary key (id) );")
        await self.client.execute("insert into user(id, name) values (?, ?);", "1", "user1")
        cursor = await self.client.execute("select * from user where id = ?;", "1")
        user = self.client.convert(await cursor.fetchone(), UserModel)
        self.assertEqual(user.id, "1")
        self.assertEqual(user.name, "user1")
        await self.client.execute("insert into user(id, name) values (?, ?);", "2", "user2")
        cursor = await self.client.execute("select * from user;")
        row_list = await cursor.fetchall()
        user_list = self.client.convert(row_list, UserModel)
        print(user_list)
        self.assertEqual(len(user_list), 2)
        self.assertEqual(user_list[1].id, "2")


class TestDBManager(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # 清空全局注册表
        DBModel.__subclass_table__ = []
        UpgradeSQL._register = []
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db_manager = DBManager(db_path=self.db_path)
        self.client = AsyncDBClient(db_path=self.db_path)

    async def asyncTearDown(self):
        if self.client.connection is not None:
            await self.client.close()
        shutil.rmtree(self.tmp_dir)

    async def test_create_all_success(self):
        class UserModel(DBModel):
            __table_name__ = "user"
            id: str = DBField(primary_key=True)
            name: str

        await self.db_manager.create_all()
        await self.client.connect()
        cursor = await self.client.execute(
            "select name from sqlite_master where type=? and name=?", "table", "user"
        )
        row = await cursor.fetchone()
        self.assertEqual(row[0], "user")

    async def test_user_version(self):
        version = await self.db_manager.user_version()
        self.assertEqual(version, 0)

    @patch("star_rail.database.sqlite.DATABASE_VERSION", new=2)
    async def test_upgrade_version_success(self):
        UpgradeSQL(
            1,
            [
                "create table if not exists user (id, name, primary key (id));",
            ],
        )
        UpgradeSQL(
            2,
            [
                "alter table user add column age;",
            ],
        )
        self.assertEqual(len(UpgradeSQL._register), 2)
        await self.db_manager.upgrade_database()
        await self.client.connect()
        cursor = await self.client.execute("pragma table_info(user);")
        column_list = await cursor.fetchall()
        self.assertEqual(len(column_list), 3)
        self.assertTrue({"id", "name", "age"}, set(column[1] for column in column_list))

    @patch("star_rail.database.sqlite.DATABASE_VERSION", new=0)
    async def test_upgrade_version_no_opt(self):
        UpgradeSQL(
            1,
            [
                "create table if not exists user (id, name, primary key (id));",
            ],
        )
        with patch.object(
            DBManager, "_perform_upgrade_script", new_callable=AsyncMock
        ) as mock_perform_sql:
            await self.db_manager.upgrade_database()
            mock_perform_sql.assert_not_called()
