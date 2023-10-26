import unittest

from star_rail.module.api_helper import Salt, gen_ds_v1, gen_ds_v2


class TestDynamicSecret(unittest.TestCase):
    def test_create_v2(self):
        param = {"uid": "300597441"}
        ds = gen_ds_v2(Salt.X4, param)
        self.assertIsNotNone(ds)

    def test_create_v1(self):
        ds = gen_ds_v1(Salt.X6)
        self.assertIsNotNone(ds)
