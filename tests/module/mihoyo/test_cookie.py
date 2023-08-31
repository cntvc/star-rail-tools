import unittest

from star_rail.module.mihoyo.cookie import Cookie


class TestCookie(unittest.TestCase):
    def test_cookie_parse_success(self):
        ck_str = "login_ticket=a;login_uid=b;other=c; mid=s"
        cookie = Cookie().parse(ck_str)
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie.verify_login_ticket())

    def test_create_cookie_success(self):
        ck_dict = {
            "ltuid": "123",
            "login_uid": "acxx",
        }
        cookie = Cookie(**ck_dict)
        self.assertIsNotNone(cookie)
        self.assertFalse(cookie.verify_login_ticket())

    def test_cookie_ne(self):
        ck_dict_1 = {
            "ltuid": "123",
            "login_uid": "acxx",
        }
        ck_dict_2 = {
            "ltuid": "123",
            "login_uid": "acxx",
        }
        ck_dict_3 = {
            "ltuid": "1234",
            "login_uid": "acxx",
        }
        ck_1 = Cookie(**ck_dict_1)
        ck_2 = Cookie(**ck_dict_2)
        ck_3 = Cookie(**ck_dict_3)
        self.assertEqual(ck_1, ck_2)
        self.assertNotEqual(ck_1, ck_3)
