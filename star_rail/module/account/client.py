import os

import pyperclip

from star_rail.config.settings import settings
from star_rail.module.base import BaseClient
from star_rail.utils.logger import logger

from .account import Account
from .cookie import Cookie
from .mapper import AccountMapper
from .repository import AccountRepository

__all__ = ["AccountClient"]


class AccountClient(BaseClient):
    async def init_default_account(self):
        logger.debug("Init default account.")
        if not settings.DEFAULT_UID:
            return
        self.user = Account(settings.DEFAULT_UID)
        result = await self.user.load_profile()
        if not result:
            # 本地配置文件记录了但数据库无数据
            self.user = None
            settings.DEFAULT_UID = ""
            settings.save_config()

    async def login(self, uid: str):
        self.user = Account(uid)
        load_profile_result = await self.user.load_profile()
        if not load_profile_result:
            await self.user.save_profile()
        settings.DEFAULT_UID = uid
        settings.save_config()
        logger.debug("Login: {}", uid)

    async def create_account_by_uid(self, uid: str):
        """根据UID创建一个账号"""
        account_mapper = await AccountMapper.query_by_uid(uid)
        if not account_mapper:
            await Account(uid).save_profile()
        return uid

    async def parse_account_cookie(self):
        logger.debug("Add cookies to account.")
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)

        if cookie.empty():
            logger.debug("Empty cookies.")
            return False

        self.user.update_cookie(cookie)
        await self.user.save_profile()
        return True

    async def delete_account(self, uid: str):
        await AccountRepository().delete_account(uid)
        user = Account(uid)
        os.remove(user.gacha_record_analyze_path)

    @staticmethod
    async def get_uid_list():
        return await AccountMapper.query_all_uid()

    def logout(self):
        self.user = None
