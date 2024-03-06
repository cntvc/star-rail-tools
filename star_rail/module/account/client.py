import pyperclip

from star_rail.config.settings import settings
from star_rail.module import routes
from star_rail.module.base import BaseClient
from star_rail.module.types import GameBiz, GameType
from star_rail.utils.logger import logger

from ..helper import Header, request
from .account import Account
from .cookie import Cookie
from .mapper import AccountMapper
from .model import GameRecordCard, UserGameRecordCards

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
        opt_status = await self.user.load_profile()
        if not opt_status:
            await self.user.save_profile()
        settings.DEFAULT_UID = uid
        settings.save_config()
        logger.debug("Login: {}", uid)

    async def create_account_by_uid(self, uid: str):
        """根据UID创建一个账户"""
        account_mapper = await AccountMapper.query_by_uid(uid)
        if not account_mapper:
            await Account(uid).save_profile()
        return uid

    async def parse_account_cookie(self):
        """解析Cookie并将其关联到对应账户，若账户不存在则会创建一个账户"""
        logger.debug("Add cookies to account.")
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)

        if cookie.empty():
            logger.debug("Empty cookies.")
            return None
        if not cookie.empty_login_ticket():
            logger.debug("Invalid cookies.")
            return None
        if not cookie.empty_stoken():
            await cookie.refresh_multi_token(self.user.game_biz)
        if not cookie.empty_cookie_token():
            await cookie.refresh_cookie_token(self.user.game_biz)
        roles = await AccountClient.get_game_record_card(cookie)
        user = None
        for role in roles.list:
            if not AccountClient.is_hsr_role(role):
                continue

            user = Account(uid=role.game_role_id)

            user.cookie = cookie
            await user.save_profile()
        return user.uid

    @staticmethod
    def is_hsr_role(role: GameRecordCard):
        """是否为星穹铁道账户"""
        return role.game_id == GameType.STAR_RAIL.value

    @staticmethod
    async def get_game_record_card(cookie: Cookie):
        param = {"uid": cookie.account_id}

        header = Header.create_header("PC")
        header.set_ds("v2", Header.Salt.X4, param)

        data = await request(
            method="GET",
            url=routes.GAME_RECORD_CARD_URL.get_url(GameBiz.CN),
            headers=header.value,
            params=param,
            cookies=cookie.model_dump("all"),
        )
        return UserGameRecordCards(**data)

    async def delete_account(self, uid: str):
        await AccountMapper.delete_account(uid)

    @staticmethod
    async def get_uid_list():
        return await AccountMapper.query_all_uid()
