import unittest

from star_rail.module.account.cookie import Cookie


class TestCookie(unittest.TestCase):
    def setUp(self) -> None:
        self.cookie = Cookie(
            login_ticket="test_login_ticket",
            login_uid="test_uid",
            account_id="test_uid",
            cookie_token="test_cookie_token",
            ltoken="test_ltoken",
            ltuid="test_uid",
            mid="test_mid",
            stoken="test_stoken",
            stuid="test_uid",
        )

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

    def test_verify_login_ticket(self):
        self.assertTrue(self.cookie.verify_login_ticket())

        self.cookie.login_ticket = ""
        self.assertFalse(self.cookie.verify_login_ticket())

    def test_verify_stoken(self):
        self.assertTrue(self.cookie.verify_stoken())

        self.cookie.stoken = ""
        self.assertFalse(self.cookie.verify_stoken())

    def test_verify_cookie_token(self):
        self.assertTrue(self.cookie.verify_cookie_token())

        self.cookie.cookie_token = ""
        self.assertFalse(self.cookie.verify_cookie_token())

    def test_model_dump(self):
        dump_all = self.cookie.model_dump()
        self.assertEqual(
            dump_all,
            {
                "login_ticket": "test_login_ticket",
                "login_uid": "test_uid",
                "account_id": "test_uid",
                "cookie_token": "test_cookie_token",
                "ltoken": "test_ltoken",
                "ltuid": "test_uid",
                "mid": "test_mid",
                "stoken": "test_stoken",
                "stuid": "test_uid",
            },
        )

        dump_web = self.cookie.model_dump(include="web")
        self.assertEqual(dump_web, {"login_ticket": "test_login_ticket", "login_uid": "test_uid"})

    def test_is_empty_cookie(self):
        cookie = Cookie()
        self.assertTrue(cookie.is_empty())
        cookie.account_id = "sss"
        self.assertFalse(cookie.is_empty())
