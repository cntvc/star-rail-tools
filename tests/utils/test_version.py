import unittest

from star_rail.utils.version import compare_versions


class TestVersion(unittest.TestCase):
    def test_compare_version(self):
        self.assertEqual(compare_versions("1.0.0", "1.1.0"), -1)
        self.assertEqual(compare_versions("1.12.0", "1.12.0"), 0)
        self.assertEqual(compare_versions("1.12.1", "1.8.3"), 1)
