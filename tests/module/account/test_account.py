import unittest

from star_rail.module import Account


class TestAccount(unittest.TestCase):
    def test_account_eq(self):
        user1 = Account(uid="123456789")
        user2 = Account(uid="123456789")
        user3 = Account(uid="223456789")
        self.assertNotEqual(user1, user3)
        self.assertEqual(user1, user2)
