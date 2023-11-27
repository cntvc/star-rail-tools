import base64
import re
from pathlib import Path

import pyperclip
from pydantic import BaseModel, ValidationError, field_serializer, field_validator, model_validator

from star_rail import constants
from star_rail.config.settings import settings
from star_rail.core import request
from star_rail.module import routes
from star_rail.module.header import Header
from star_rail.module.types import GameBiz, GameType, Region
from star_rail.utils.logger import logger
from star_rail.utils.security import AES128

from .cookie import Cookie
from .mapper import AccountMapper
from .model import GameRecordCard, UserGameRecordCards

__all__ = ["Account", "AccountClient"]


def verify_uid_format(v):
    if Account.verify_uid(v):
        return v
    raise ValidationError(f"Invalid uid format: {v}")


_UID_RE = re.compile("^[1-9][0-9]{8}$")


class Account(BaseModel):
    uid: str
    cookie: Cookie = Cookie()

    # 以下成员根据 uid 初始化
    region: Region = None
    game_biz: GameBiz = None

    gacha_record_xlsx_path: Path = ""
    gacha_record_analyze_path: Path = ""
    srgf_path: Path = ""

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    def __init__(self, uid: str, **data):
        super().__init__(uid=uid, **data)

    @model_validator(mode="after")
    def init_param(self):
        self._init_datafile_path()
        self._init_game_biz()
        self._init_region()

    def _init_datafile_path(self):
        self.gacha_record_xlsx_path = Path(
            constants.ROOT_PATH, self.uid, f"GachaRecord_{self.uid}.xlsx"
        )
        self.srgf_path = Path(constants.ROOT_PATH, self.uid, f"GachaRecord_SRGF_{self.uid}.json")
        self.gacha_record_analyze_path = Path(
            constants.TEMP_PATH, f"GachaRecordAnalyze_{self.uid}.json"
        )

    def _init_game_biz(self):
        self.game_biz = GameBiz.get_by_uid(self.uid)

    def _init_region(self):
        self.region = Region.get_by_uid(self.uid)

    @field_serializer("region")
    def serialize_region(self, region: Region):
        return region.value

    @field_serializer("game_biz")
    def serialize_game_biz(self, game_biz: GameBiz):
        return game_biz.value

    def model_dump(self, include={"uid", "cookie", "region", "game_biz"}, **kwargs):
        return super().model_dump(include=include, **kwargs)

    async def load_profile(self) -> bool:
        logger.debug("Load profile. Account: {}", self.uid)
        account_mapper = await AccountMapper.query_by_uid(self.uid)
        if account_mapper is None:
            return False

        from . import converter

        local_account = converter.mapper_to_account(account_mapper)

        def decrypt_cookie(cookie: Cookie) -> Cookie:
            # 如果 cookie 为默认值（空），则不进行解密
            cookie_dict = cookie.model_dump("all")
            if not cookie_dict:
                return cookie
            key = base64.b64decode(settings.ENCRYPT_KEY)
            aes = AES128(key)
            return Cookie(**{c_k: aes.decrypt(c_v) for c_k, c_v in cookie_dict.items()})

        try:
            local_account.cookie = decrypt_cookie(local_account.cookie)
        except Exception:
            # 如果解密失败，key失效，重置 key 和 Cookie
            settings.ENCRYPT_KEY = ""
            settings.save_config()
            self.cookie = Cookie()
            self.save_profile()
            return True

        for k in local_account.model_fields_set:
            setattr(self, k, getattr(local_account, k))
        return True

    async def save_profile(self) -> bool:
        logger.debug("Save profile. Account: {}", self.uid)

        def encrypt_cookie(cookie: Cookie) -> Cookie:
            # 加密时，如果key不存在则生成新key
            # 当cookie中value全部为默认值（即未设置Cookie）则不进行加密
            # 否则使用该key对cookie的value加密，返回加密后的Cookie对象

            if not settings.ENCRYPT_KEY:
                settings.ENCRYPT_KEY = AES128.generate_aes_key()
                settings.save_config()

            cookie_dict = cookie.model_dump("all")
            if not cookie_dict:
                return cookie
            key = base64.b64decode(settings.ENCRYPT_KEY)
            aes = AES128(key)
            return Cookie(**{k: aes.encrypt(v) for k, v in cookie_dict.items()})

        insert_user = self.model_copy(deep=True, update={"cookie": encrypt_cookie(self.cookie)})
        from . import converter

        account_mapper = converter.account_to_mapper(insert_user)
        cnt = await AccountMapper.add_account(account_mapper)
        return True if cnt else False

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and _UID_RE.fullmatch(v) is not None

    def __eq__(self, other: "Account"):
        return self.uid == other.uid and self.cookie == other.cookie

    def __ne__(self, other: "Account"):
        return self.uid != other.uid or self.cookie != other.cookie


class AccountClient:
    user: Account

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

    async def create_account_with_cookie(self):
        logger.debug("Add cookies to account.")
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)

        if cookie.empty():
            logger.debug("Empty cookies.")
            return None
        if not cookie.verify_login_ticket():
            logger.debug("Invalid cookies.")
            return None
        await cookie.refresh_multi_token()
        await cookie.refresh_cookie_token()
        roles = await AccountClient.get_game_record_card(cookie)
        user = None
        for role in roles.list:
            if not AccountClient.is_hsr_role(role):
                continue

            user = Account(uid=role.game_role_id)

            user.cookie = cookie
            await user.save_profile()
        return user

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
        return await AccountMapper.query_all_user()
