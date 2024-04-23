import os

import pyperclip

from star_rail.config.settings import settings
from star_rail.module import routes
from star_rail.module.base import BaseClient
from star_rail.module.types import GameBiz, GameType
from star_rail.utils.logger import logger

from ..web import Header, request
from .account import Account
from .cookie import Cookie
from .mapper import AccountMapper
from .model import GameRecordCard, UserGameRecordCards
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

    async def _handle_cookie_cn(self, cookie: Cookie):
        """解析Cookie，获取所有可更新Cookie字段"""

        if cookie.empty_login_ticket():
            logger.debug("Invalid cookies.")
            return None

        if cookie.empty_stoken():
            await cookie.refresh_multi_token(self.user.game_biz)

        if cookie.empty_cookie_token():
            await cookie.refresh_cookie_token(self.user.game_biz)

        roles = await AccountClient._get_game_record_card_cn(cookie, self.user.game_biz)

        for role in roles.list:
            if not AccountClient.is_hsr_role(role):
                continue
            if role.game_role_id == self.user.uid:
                return cookie
        return None

    async def _handle_cookie_os(self, cookie: Cookie):
        return cookie

    async def parse_account_cookie(self):
        logger.debug("Add cookies to account.")
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)

        if cookie.empty():
            logger.debug("Empty cookies.")
            return False

        if self.user.game_biz == GameBiz.GLOBAL:
            cookie = await self._handle_cookie_os(cookie)
        elif self.user.game_biz == GameBiz.CN:
            cookie = await self._handle_cookie_cn(cookie)
        else:
            raise AssertionError("Invalid game_biz")

        if not cookie:
            return False

        self.user.cookie = cookie
        await self.user.save_profile()
        return True

    @staticmethod
    def is_hsr_role(role: GameRecordCard):
        """是否为星穹铁道账号"""
        return role.game_id == GameType.STAR_RAIL.value

    @staticmethod
    async def _get_game_record_card_cn(cookie: Cookie, game_biz: GameBiz):
        param = {"uid": cookie.account_id}

        header = Header.generate("PC")
        header.set_ds("v2", Header.Salt.X4, param)

        data = await request(
            method="GET",
            url=routes.GAME_RECORD_CARD_URL.get_url(game_biz),
            headers=header.headers,
            params=param,
            cookies=cookie.model_dump("all"),
        )
        return UserGameRecordCards(**data)

    async def delete_account(self, uid: str):
        await AccountRepository().delete_account(uid)
        user = Account(uid)
        os.remove(user.gacha_record_analyze_path)

    @staticmethod
    async def get_uid_list():
        return await AccountMapper.query_all_uid()

    def logout(self):
        self.user = None
