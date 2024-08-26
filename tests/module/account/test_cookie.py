import unittest
from unittest.mock import AsyncMock, patch

from star_rail.module.account.cookie import Cookie
from star_rail.module.types import GameBiz


class TestCookie(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.cookie = Cookie(
            account_id="account_id",
            account_id_v2="account_id",
            account_mid_v2="account_mid_v2",
            cookie_token="cookie_token",
            cookie_token_v2="cookie_token_v2",
            login_ticket="login_ticket",
            login_uid="account_id",
            ltmid_v2="account_mid_v2",
            ltoken="ltoken",
            ltoken_v2="ltoken_v2",
            ltuid="account_id",
            ltuid_v2="account_id",
            stoken="stoken",
            stuid="account_id",
        )

    def test_cookie_paese_failed(self):
        with self.subTest(msg="type error"):
            with self.assertRaises(AssertionError):
                Cookie.parse(1)

    def test_cookie_parse_success(self):
        ck_str = "login_ticket=a;login_uid=b;other=c; ltmid=s"
        has_value = (
            "login_ticket",
            "login_uid",
            "stuid",
            "ltuid",
            "ltuid_v2",
            "account_id",
            "account_id_v2",
            "ltmid",
            "ltmid_v2",
            "account_mid",
            "account_mid_v2",
            "mid",
        )
        cookie = Cookie.parse(ck_str)
        for k in cookie.model_fields_set:
            if k in has_value:
                self.assertTrue(getattr(cookie, k))
            else:
                self.assertEqual(getattr(cookie, k), "")

    def test_cookie_parse_empty(self):
        ck_str = ""
        cookie = Cookie.parse(ck_str)
        for k in cookie.model_fields_set:
            self.assertEqual(getattr(cookie, k), "")

    def test_verify_stoken(self):
        self.assertFalse(self.cookie.empty_stoken())

        self.cookie.stoken = ""
        self.assertTrue(self.cookie.empty_stoken())

    def test_verify_cookie_token(self):
        self.assertFalse(self.cookie.empty_cookie_token())

        self.cookie.cookie_token = ""
        self.assertFalse(self.cookie.empty_cookie_token())
        self.cookie.cookie_token_v2 = ""
        self.assertTrue(self.cookie.empty_cookie_token())

    def test_model_dump(self):
        dump_all = self.cookie.model_dump()
        self.assertEqual(
            dump_all,
            {
                "account_id": "account_id",
                "account_id_v2": "account_id",
                "account_mid": "account_mid_v2",
                "account_mid_v2": "account_mid_v2",
                "cookie_token": "cookie_token",
                "cookie_token_v2": "cookie_token_v2",
                "login_ticket": "login_ticket",
                "login_uid": "account_id",
                "ltmid_v2": "account_mid_v2",
                "ltmid": "account_mid_v2",
                "ltoken": "ltoken",
                "ltoken_v2": "ltoken_v2",
                "ltuid": "account_id",
                "ltuid_v2": "account_id",
                "stoken": "stoken",
                "stuid": "account_id",
                "mid": "account_mid_v2",
            },
        )

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
