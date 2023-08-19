import typing
import unittest

from star_rail import exceptions as error

# 导入你的模块
from star_rail.database.database import (
    DataBaseClient,
    DataBaseField,
    DataBaseModel,
    ModelAnnotation,
    model_convert_item,
    model_convert_list,
)


class TestModelAnnotation(unittest.TestCase):
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

        self.assertRaises(error.DataBaseModelError, ModelAnnotation.parse, TestModel)


class TestDataBaseClient(unittest.TestCase):
    def test_insert(self):
        class UserModel(DataBaseModel):
            __table_name__ = "user"
            id: str = DataBaseField(primary_key=True)
            name: str
            age: int

        client = DataBaseClient(":memory:")
        client.create_all()

        item = UserModel(id="1", name="Alice", age=25)
        client.insert(item, "ignore")
        client.commit()
        result = client.select("SELECT * FROM user where id = '1';").fetchone()
        self.assertEqual(result["name"], "Alice")
        self.assertEqual(result["age"], 25)

    def test_model_convert(self):
        class UserModel(DataBaseModel):
            __table_name__ = "user"
            id: str = DataBaseField(primary_key=True)
            name: str
            age: int

        client = DataBaseClient(":memory:")
        client.create_all()
        items = [
            UserModel(id="1", name="Alice", age=78),
            UserModel(id="2", name="Bob", age=30),
        ]
        client.insert_batch(items, "update")
        client.commit()
        results = client.select("SELECT * FROM user;").fetchall()
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Alice")
        self.assertEqual(results[1]["name"], "Bob")

        # test convert list
        users = model_convert_list(results, UserModel)
        self.assertIsNotNone(users)
        self.assertTrue(isinstance(users, typing.List))
        self.assertEqual(users[0].id, "1")
        self.assertEqual(users[0].age, 78)

        # test convert item
        row = client.select("select * from user where id = '1';").fetchone()
        user = model_convert_item(row, UserModel)
        self.assertTrue(isinstance(user, UserModel))

        # test convert item is None
        row = client.select("select * from user where id = '4';").fetchone()
        user = model_convert_item(row, UserModel)
        self.assertIsNone(user)
        client.close_all()
