import unittest

from star_rail.utils.version import compare_versions


class TestVersion(unittest.TestCase):
    def test_compare_version(self):
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), -1)
        self.assertEqual(compare_versions("1.0.0", "1.0.11"), -1)
        self.assertEqual(compare_versions("1.0.0", "1.10.0"), -1)
        self.assertEqual(compare_versions("1.0.0", "11.0.11"), -1)
        self.assertEqual(compare_versions("1.0.0", "1.1.0.dev1"), -1)
        self.assertEqual(compare_versions("1.0.0dev1", "1.1.0.dev1"), -1)

        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("11.0.0", "11.0.0"), 0)
        self.assertEqual(compare_versions("1.10.120", "1.10.120"), 0)
        self.assertEqual(compare_versions("1.1.1", "1.1.1dev1"), 0)
        self.assertEqual(compare_versions("1.1.1dev2", "1.1.1dev2"), 0)

        self.assertEqual(compare_versions("0.0.2", "0.0.1"), 1)
        self.assertEqual(compare_versions("0.10.0", "0.0.1"), 1)
        self.assertEqual(compare_versions("10.0.0", "0.0.1"), 1)
        self.assertEqual(compare_versions("100.10.2", "100.10.1"), 1)
        self.assertEqual(compare_versions("100.10.2", "100.10.1"), 1)
        self.assertEqual(compare_versions("1.1.1dev1", "1.1.0dev1"), 1)
        self.assertEqual(compare_versions("1.1.1dev3", "1.1.0dev1"), 1)
