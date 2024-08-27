import unittest

from star_rail.utils.version import Version


class TestVersion(unittest.TestCase):
    def test_compare_version(self):
        self.assertTrue(Version("1.0.0") < Version("1.0.1"))
        self.assertTrue(Version("1.0.0") < Version("1.0.11"))
        self.assertTrue(Version("1.0.0") < Version("1.10.0"))
        self.assertTrue(Version("1.0.0") < Version("11.0.11"))
        self.assertTrue(Version("1.0.0") < Version("1.1.0.dev1"))
        self.assertTrue(Version("1.0.0.dev1") < Version("1.1.0.dev1"))

        self.assertEqual(Version("1.0.0"), Version("1.0.0"))
        self.assertEqual(Version("11.0.0"), Version("11.0.0"))
        self.assertEqual(Version("1.10.120"), Version("1.10.120"))

        self.assertTrue(Version("0.0.2") > Version("0.0.1"))
        self.assertTrue(Version("0.10.0") > Version("0.0.1"))
        self.assertTrue(Version("10.0.0") > Version("0.0.1"))
        self.assertTrue(Version("100.10.2") > Version("100.10.1"))
        self.assertTrue(Version("1.1.1.dev2") > Version("1.1.1.dev1"))
        self.assertTrue(Version("1.1.2.dev1") > Version("1.1.1.dev1"))
        self.assertTrue(Version("1.1.1") > Version("1.1.1.dev1"))
        self.assertTrue(Version("1.1.2") > Version("1.1.1.dev1"))
