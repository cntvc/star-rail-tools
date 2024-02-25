import unittest
from unittest.mock import AsyncMock, patch

from star_rail.module.account.cookie import Cookie
from star_rail.module.types import GameBiz


class TestCookie(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.cookie = Cookie(
            login_ticket="test_login_ticket",
            login_uid="test_uid",
            account_id="test_uid",
            cookie_token="test_cookie_token",
            ltoken="test_ltoken",
            ltuid="test_uid",
            ltmid="test_mid",
            stoken="test_stoken",
            stuid="test_uid",
        )

    def test_cookie_paese_failed(self):
        ck_str = 1
        with self.assertRaises(AssertionError):
            Cookie.parse(ck_str)

    def test_cookie_parse_success(self):
        ck_str = "login_ticket=a;login_uid=b;other=c; ltmid=s"
        has_value = (
            "login_ticket",
            "login_uid",
            "stuid",
            "ltuid",
            "account_id",
            "account_mid",
            "ltmid",
        )
        cookie = Cookie.parse(ck_str)
        for k in cookie.model_fields_set:
            if k in has_value:
                self.assertTrue(getattr(cookie, k))
            else:
                self.assertEqual(getattr(cookie, k), "")
        self.assertTrue(cookie.stuid == cookie.ltuid == cookie.login_uid == cookie.account_id)

    def test_cookie_parse_success_ckv2(self):
        ck_str = "login_ticket_v2=a;login_uid_v2=b;other=c; ltmid_v2=s"
        has_value = (
            "login_ticket",
            "login_uid",
            "stuid",
            "ltuid",
            "account_id",
            "account_mid",
            "ltmid",
        )
        cookie = Cookie.parse(ck_str)
        for k in cookie.model_fields_set:
            if k in has_value:
                self.assertTrue(getattr(cookie, k))
            else:
                self.assertEqual(getattr(cookie, k), "")
        self.assertTrue(cookie.stuid == cookie.ltuid == cookie.login_uid == cookie.account_id)
        self.assertEqual(cookie.ltmid, "s")

    def test_cookie_parse_empty(self):
        ck_str = ""
        cookie = Cookie.parse(ck_str)
        for k in cookie.model_fields_set:
            self.assertEqual(getattr(cookie, k), "")

    def test_verify_login_ticket(self):
        self.assertTrue(self.cookie.empty_login_ticket())

        self.cookie.login_ticket = ""
        self.assertFalse(self.cookie.empty_login_ticket())

    def test_verify_stoken(self):
        self.assertTrue(self.cookie.empty_stoken())

        self.cookie.stoken = ""
        self.assertFalse(self.cookie.empty_stoken())

    def test_verify_cookie_token(self):
        self.assertTrue(self.cookie.empty_cookie_token())

        self.cookie.cookie_token = ""
        self.assertFalse(self.cookie.empty_cookie_token())

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
                "stoken": "test_stoken",
                "stuid": "test_uid",
                "account_mid": "test_mid",
                "ltmid": "test_mid",
            },
        )

        dump_web = self.cookie.model_dump(include="web")
        self.assertEqual(
            dump_web,
            {
                "login_ticket": "test_login_ticket",
                "login_uid": "test_uid",
                "account_id": "test_uid",
                "account_mid": "test_mid",
            },
        )

    async def test_refresh_multi_token(self):
        cookie = Cookie()
        cookie.login_ticket = "xxx_login_ticket"
        cookie.login_uid = "123456789"

        with patch(
            "star_rail.module.account.cookie.request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {
                "list": [
                    {"name": "stoken", "token": "xx_stoken"},
                    {"name": "ltoken", "token": "xxxx_ltoken"},
                ]
            }

            # Act
            await cookie.refresh_multi_token(GameBiz.CN)

            # Assert
            self.assertEqual(cookie.stoken, "xx_stoken")
            self.assertEqual(cookie.ltoken, "xxxx_ltoken")

    async def test_refresh_cookie_token(self):
        # Arrange
        cookie = Cookie()
        cookie.login_uid = "123456789"
        cookie.stoken = "stoken"

        # Mock the request function
        with patch(
            "star_rail.module.account.cookie.request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = {"cookie_token": "xxcookie_token"}

            # Act
            await cookie.refresh_cookie_token(GameBiz.CN)

            # Assert
            self.assertEqual(cookie.cookie_token, "xxcookie_token")
