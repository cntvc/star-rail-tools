import os
import shutil
import tempfile
import unittest
from functools import partial

from star_rail import exceptions as error

# 导入你的模块
from star_rail.database.database import (
    DataBaseClient,
    DataBaseField,
    DataBaseModel,
    DBManager,
    ModelAnnotation,
    model_convert_item,
    model_convert_list,
)


class TestModelAnnotation(unittest.TestCase):
    def setUp(self) -> None:
        # 清空全局注册表，否则影响其他测试用例
        DataBaseModel.__subclass_table__ = []

    def test_parse(self):
        class TestModel(DataBaseModel):
            __table_name__ = "test_table"
            name: str = DataBaseField(primary_key=True)
            age: int

        annotation = ModelAnnotation.parse(TestModel)
        self.assertIsNotNone(annotation)
        self.assertEqual(annotation.table_name, "test_table")
        self.assertSetEqual(annotation.column, {"name", "age"})
        self.assertSetEqual(annotation.primary_key, {"name"})

    def test_parse_without_table_name(self):
        class TestModel(DataBaseModel):
            name: str
            age: int

        self.assertRaises(error.DataBaseError, ModelAnnotation.parse, TestModel)


class TestDataBaseClient(unittest.TestCase):
    def setUp(self) -> None:
        # 清空全局注册表，否则影响其他测试用例
        DataBaseModel.__subclass_table__ = []
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.client = DataBaseClient(self.db_path)
        self.db_manager = DBManager(self.client)

    def tearDown(self) -> None:
        self.client.close_all()
        shutil.rmtree(self.tmp_dir)

    def test_insert(self):
        class UserModel(DataBaseModel):
            __table_name__ = "user"
            id: str = DataBaseField(primary_key=True)
            name: str
            age: int

        self.db_manager.create_all()

        client = self.client
        client.connection()

        item = UserModel(id="1", name="Alice", age=25)
        client.insert(item, "ignore")

        result = client.execute("SELECT * FROM user where id = '1';").fetchone()
        self.assertEqual(result["name"], "Alice")
        self.assertEqual(result["age"], 25)

    def test_insert_batch(self):
        class UserModel(DataBaseModel):
            __table_name__ = "user"
            id: str = DataBaseField(primary_key=True)
            name: str
            age: int

        items = [
            UserModel(id="1", name="Alice", age=78),
            UserModel(id="2", name="Bob", age=30),
            UserModel(id="3", name="Charlie", age=13),
            UserModel(id="4", name="Snoopy", age=5),
        ]

        self.db_manager.create_all()
        client = self.client
        client.connection()
        # 存在则忽略
        client.insert_batch(items[:3], mode="ignore")

        results = client.execute("SELECT * FROM user;").fetchall()
        self.assertEqual(len(results), 3)
        self.assertEqual(results[2]["name"], "Charlie")

        items.append(UserModel(id="2", name="Bob_new", age=31))
        # 存在则更新
        client.insert_batch(items, mode="update")

        results = client.execute("SELECT * FROM user;").fetchall()
        self.assertEqual(len(results), 4)
        for r in results:
            if r["id"] == "2":
                self.assertEqual(r["name"], "Bob_new")

    def test_model_convert(self):
        class UserModel(DataBaseModel):
            __table_name__ = "user"
            id: str = DataBaseField(primary_key=True)
            name: str
            age: int

        self.db_manager.create_all()
        client = self.client
        client.connection()

        items = [
            UserModel(id="1", name="Alice", age=78),
            UserModel(id="2", name="Bob", age=30),
        ]
        client.insert_batch(items, "update")

        results = client.execute("SELECT * FROM user;").fetchall()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Alice")
        self.assertEqual(results[1]["name"], "Bob")

        # test convert list
        users = model_convert_list(results, UserModel)
        self.assertIsNotNone(users)
        self.assertTrue(isinstance(users, list))
        self.assertEqual(users[0].id, "1")
        self.assertEqual(users[0].age, 78)

        # test convert item
        row = client.execute("select * from user where id = '1';").fetchone()
        user = model_convert_item(row, UserModel)
        self.assertTrue(isinstance(user, UserModel))

        # test convert item is None
        row = client.execute("select * from user where id = '4';").fetchone()
        user = model_convert_item(row, UserModel)
        self.assertIsNone(user)


class TestDataBaseManager(unittest.TestCase):
    def setUp(self):
        # 清空全局注册表，否则影响其他测试用例
        DataBaseModel.__subclass_table__ = []

        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test.db")
        self.db_client = DataBaseClient(self.db_path)
        self.db_manager = DBManager(self.db_client)

    def test_create_all(self):
        class TestModel(DataBaseModel):
            __table_name__ = "test_table"
            field1: str = DataBaseField(primary_key=True)

        self.db_manager.create_all()

        # 打开数据库并查询表是否创建成功
        import sqlite3

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(test_table)")
        table_info = cursor.fetchall()
        conn.close()

        self.assertTrue(table_info)

    def test_set_user_version(self):
        version = self.db_manager.get_user_version()
        self.assertEqual(version, 0)
        # 设置数据库版本为2
        self.db_manager.set_user_version(2)

        # 检查数据库版本
        version = self.db_manager.get_user_version()
        self.assertEqual(version, 2)

    def test_update_to_version(self):
        def _upgrade_to_version_1(self):
            pass

        # 注册升级函数
        self.db_manager._upgrade_to_version_1 = partial(_upgrade_to_version_1, self.db_manager)
        self.db_manager._upgrade_to_version_2 = partial(_upgrade_to_version_1, self.db_manager)
        DBManager.DATABASE_USER_VERSION = 2
        # 设置当前数据库版本为0
        self.db_manager.set_user_version(0)
        self.assertEqual(self.db_manager.get_user_version(), 0)
        # 运行升级函数并检查版本是否升级
        self.db_manager.update_to_version()
        version = self.db_manager.get_user_version()
        self.assertEqual(version, 2)
