import unittest

from star_rail.module.mihoyo.header import DynamicSecret, Salt


class TestDynamicSecret(unittest.TestCase):
    def test_create_v2(self):
        param = {"uid": "300597441"}
        ds = DynamicSecret(Salt.X4).gen_ds_v2(param)
        self.assertIsNotNone(ds)

    def test_create_v1(self):
        ds = DynamicSecret(Salt.X6).gen_ds_v1()
        self.assertIsNotNone(ds)
