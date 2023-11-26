import unittest
from unittest.mock import AsyncMock, Mock, patch

from star_rail.config import settings
from star_rail.config.settings import BaseSetting
from star_rail.module import Account
from star_rail.module.account.cookie import Cookie
from star_rail.module.account.mapper import AccountMapper
from star_rail.utils.security import AES128


class TestAccount(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        pass

    async def test_load_profile_false(self):
        uid = "123456789"
        account = Account(uid=uid)

        with patch.object(
            AccountMapper, "query_by_uid", new_callable=AsyncMock
        ) as mock_query_by_uid:
            mock_query_by_uid.return_value = None
            result = await account.load_profile()
            self.assertFalse(result)

    async def test_load_profile_with_decrypt(self):
        uid = "123456789"
        account = Account(uid=uid)

        with patch.object(
            AccountMapper, "query_by_uid", new_callable=AsyncMock
        ) as mock_query_by_uid:
            test_cookie = Cookie(
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
            mock_query_by_uid.return_value = AccountMapper(
                uid=uid,
                cookie=test_cookie.model_dump_json(exclude_defaults=True),
                region="prod_gf_cn",
                game_biz="hkrpg_cn",
            )
            with patch.object(AES128, "decrypt", return_value="decrypted_value"):
                with patch.object(settings, "ENCRYPT_KEY", new=AES128.generate_aes_key()):
                    result = await account.load_profile()

                    self.assertTrue(result)
                    self.assertEqual(account.uid, uid)

                    for k in account.cookie.model_fields_set:
                        self.assertEqual(getattr(account.cookie, k), "decrypted_value")

    async def test_load_profile_with_no_decrypt(self):
        uid = "123456789"
        account = Account(uid=uid)

        with patch.object(
            AccountMapper, "query_by_uid", new_callable=AsyncMock
        ) as mock_query_by_uid:
            test_cookie = Cookie(
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
            mock_query_by_uid.return_value = AccountMapper(
                uid=uid,
                cookie=test_cookie.model_dump_json(exclude_defaults=True),
                region="prod_gf_cn",
                game_biz="hkrpg_cn",
            )
            with patch.object(AES128, "decrypt", return_value="decrypted_value"):
                with patch.object(settings, "ENCRYPT_KEY", new=""):
                    result = await account.load_profile()

                    self.assertTrue(result)
                    self.assertEqual(account.uid, uid)

                    for k in account.cookie.model_fields_set:
                        self.assertEqual(getattr(account.cookie, k), getattr(test_cookie, k))

    async def test_save_profile_no_encrypt(self):
        uid = "123456789"
        account = Account(
            uid=uid,
            cookie=Cookie(
                login_ticket="test_login_ticket",
                login_uid="test_uid",
                account_id="test_uid",
                cookie_token="test_cookie_token",
                ltoken="test_ltoken",
                ltuid="test_uid",
                mid="test_mid",
                stoken="test_stoken",
                stuid="test_uid",
            ),
        )
        with patch.object(AccountMapper, "add_account", new_callable=AsyncMock) as mock_add_account:
            mock_add_account.return_value = 1
            with patch.object(settings, "ENCRYPT_KEY", new=""), patch.object(
                BaseSetting, "save_config", new_callable=Mock
            ) as mock_save_config:
                result = await account.save_profile()
        self.assertTrue(result)
        mock_save_config.assert_called_once()

    async def test_save_profile_encrypt(self):
        uid = "123456789"
        account = Account(uid=uid)
        with patch.object(AccountMapper, "add_account", new_callable=AsyncMock) as mock_add_account:
            mock_add_account.return_value = 1
            with patch.object(settings, "ENCRYPT_KEY", new=AES128.generate_aes_key()), patch.object(
                BaseSetting, "save_config", new_callable=Mock
            ) as mock_save_config:
                result = await account.save_profile()
        self.assertTrue(result)
        mock_save_config.assert_not_called()

    def test_model_dump(self):
        pass

    def test_account_eq(self):
        user1 = Account(uid="123456789")
        user2 = Account(uid="123456789")
        user2_4 = Account(uid="123456789", cookie=Cookie(login_uid="123456789"))
        user3 = Account(uid="223456789")

        self.assertNotEqual(user2, user2_4)
        self.assertNotEqual(user1, user3)
        self.assertEqual(user1, user2)
