import re
from pathlib import Path

import pyperclip
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from star_rail import constants
from star_rail import exceptions as error
from star_rail.config import settings
from star_rail.database import DataBaseClient
from star_rail.i18n import i18n
from star_rail.utils.functional import color_str
from star_rail.utils.log import logger
from star_rail.utils.menu import MenuItem
from star_rail.utils.security import AES128

from ..api_helper import DefaultHeader, Header, Salt, request
from ..routes import GAME_RECORD_CARD_URL
from ..types import GameBiz, GameType, Region
from .cookie import Cookie
from .mapper import CookieMapper, UserMapper
from .model import GameRecordCard, UserGameRecordCards

__all__ = ["Account", "AccountManager"]

_lang = i18n.account


def verify_uid_format(v):
    if Account.verify_uid(v):
        return v
    raise ValidationError(f"Invalid uid format: {v}")


_UID_RE = re.compile("^[1-9][0-9]{8}$")


class Account(BaseModel):
    uid: str
    """星铁账户 UID"""
    cookie: Cookie = Cookie()
    gacha_url: str = ""

    # 以下成员根据 uid 初始化
    region: str = ""
    game_biz: str = ""

    gacha_record_xlsx_path: Path = ""
    gacha_record_analyze_path: Path = ""
    srgf_path: Path = ""

    def __init__(self, uid: str, **data):
        super().__init__(uid=uid, **data)

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    _serialize_include_keys = {"cookie", "uid", "gacha_url"}

    @model_validator(mode="after")
    def init_param(self):
        self._init_datafile_path()
        self._init_game_biz()
        self._init_region()

    def _init_datafile_path(self):
        self.gacha_record_xlsx_path = Path(
            constants.ROOT_PATH, self.uid, f"GachaRecord_{self.uid}.xlsx"
        )
        self.gacha_record_analyze_path = Path(
            constants.TEMP_PATH, f"GachaRecordAnalyze_{self.uid}.json"
        )
        self.srgf_path = Path(constants.ROOT_PATH, self.uid, f"GachaRecord_SRGF_{self.uid}.json")

    def _init_game_biz(self):
        self.game_biz = GameBiz.get_by_uid(self.uid).value

    def _init_region(self):
        self.region = Region.get_by_uid(self.uid).value

    def _encrypt_cookie(self) -> dict[str, str]:
        if not settings.SALT:
            raise error.EncryptError("Empty salt value")
        # 未设置 Cookie 时无需加密
        if self.cookie.is_empty():
            return {}
        aes128 = AES128(settings.SALT)
        cookie = self.cookie.model_dump()
        return {k: aes128.encrypt(v) for k, v in cookie.items()}

    def _decrypt_cookie(self, cookie: Cookie) -> Cookie:
        if not settings.SALT:
            raise error.DecryptError("Empty salt value")
        # 未设置 Cookie 时无需解密
        if cookie.is_empty():
            return cookie
        aes128 = AES128(settings.SALT)
        for k in cookie.model_fields.keys():
            setattr(cookie, k, aes128.decrypt(getattr(cookie, k)))
        return cookie

    def save_profile(self):
        """保存数据到 user 表和 cookie 表"""
        logger.debug("save user profile")

        from . import converter as converter

        user_mapper = converter.user_to_mapper(self)
        # 如果配置文件中 Salt 值不存在，表示为旧版本升级或者配置文件被删除等其他原因，那么自动生成一个并保存
        if not settings.SALT:
            salt = AES128.generate_salt()
            settings.SALT = salt
            settings.save_config()

        encrypt_cookie = self._encrypt_cookie()
        cookie_mapper = CookieMapper(uid=self.uid, **encrypt_cookie)
        with DataBaseClient() as db:
            db.insert(user_mapper, "update")
            db.insert(cookie_mapper, "update")

    def reload_profile(self) -> bool:
        """重新加载用户数据"""
        from . import converter as converter

        logger.debug("load user profile")

        user_mapper = UserMapper.query_user(self.uid)
        if user_mapper is None:
            return False
        local_user = converter.user_mapper_to_user(user_mapper)
        local_user_cookie_mapper = CookieMapper.query_cookie(self.uid)
        local_cookie = converter.cookie_mapper_to_cookie(local_user_cookie_mapper)

        """
        加载账户基本数据时，使用配置文件中的 salt 对 cookie 解密
        如果解密错误，表示 salt 无效或出现其他错误，重置配置文件的 salt 和数据库 cookie

        如果配置文件中 Salt 值不存在，表示为旧版本升级或者配置文件被删除等其他原因，那么自动生成一个并保存
        """
        if not settings.SALT:
            salt = AES128.generate_salt()
            settings.SALT = salt
            settings.save_config()

        try:
            local_user.cookie = self._decrypt_cookie(local_cookie)
        except error.DecryptError:
            logger.debug("Decrypt cookie failed, reset data")
            settings.SALT = ""
            settings.save_config()
            empty_cookie_mapper = converter.cookie_to_cookie_mapper(self, Cookie())
            with DataBaseClient() as db:
                db.insert(empty_cookie_mapper, "update")
            local_user.cookie = Cookie()

        for k in local_user.model_fields_set:
            if k not in self._serialize_include_keys:
                continue
            v = getattr(local_user, k)
            setattr(self, k, v)
        return True

    def model_dump(self, *args, **kwargs):
        return super().model_dump(include=self._serialize_include_keys)

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and _UID_RE.fullmatch(v) is not None

    def __eq__(self, other: "Account"):
        return self.uid == other.uid and self.cookie == other.cookie

    def __ne__(self, other: "Account"):
        return self.uid != other.uid or self.cookie != other.cookie


class AccountManager:
    def __init__(self):
        self.user: Account = None

    def init_default_user(self):
        logger.debug("init default user")
        if not settings.DEFAULT_UID:
            self.user = None
            return
        self.user = Account(settings.DEFAULT_UID)
        result = self.user.reload_profile()
        if result is False:
            # 本地文件设置了默认账户数据库却不存在该账号
            self.user = None
            settings.DEFAULT_UID = ""
            settings.save_config()

    def login(self, user: str | Account):
        if isinstance(user, str):
            self.user = Account(user)
        elif isinstance(user, Account):
            self.user = user
        else:
            raise error.HsrException(i18n.error.param_type_error, type(user))

        self.user.reload_profile()
        logger.success(_lang.login_account_success, self.user.uid)
        settings.DEFAULT_UID = self.user.uid
        settings.save_config()

    def create_by_input_uid(self):
        logger.debug("create user by input uid")
        uid = _input_uid()
        if uid is None:
            return
        user = Account(uid)
        if not user.reload_profile():
            # 如果库里没有该账户，则创建
            user.save_profile()
        logger.success(_lang.add_account_success, user.uid)

    @error.err_catch(level="WARNING")
    def create_by_cookie(self):
        logger.debug("create user by cookie")
        if not settings.SALT:
            settings.SALT = AES128.generate_salt()
            settings.save_config()
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)
        if cookie is None:
            logger.warning(_lang.invalid_cookie)
            return
        if cookie.verify_login_ticket() and not cookie.verify_stoken():
            cookie.refresh_multi_token()
        cookie.refresh_cookie_token()
        roles = get_game_record_card(cookie)
        for role in roles.list:
            if not self.is_hsr_role(role):
                continue

            user = Account(uid=role.game_role_id)

            user.cookie = cookie
            user.save_profile()

            # 如果与当前登陆的账号一致，更新内存数据
            if self.user is not None and self.user.uid == user.uid:
                self.user = user
                logger.success(_lang.update_cookie_success, user.uid)
            else:
                logger.success(_lang.add_account_success, user.uid)

    def delete(self, user: Account):
        """# TODO 删除user的所有表数据"""

    def is_hsr_role(self, role: GameRecordCard):
        """是否为星穹铁道账户"""
        return role.game_id == GameType.STAR_RAIL.value

    def get_uid_list(self):
        user_list = UserMapper.query_all()
        if user_list is None:
            return []
        return [user.uid for user in user_list]

    def get_account_status_desc(self):
        if self.user is not None:
            return _lang.current_account.format(color_str(self.user.uid, color="green"))
        return _lang.without_account

    def create_account_menu(self):
        menu_list = [
            MenuItem(title=_lang.menu.add_by_game_uid, options=lambda: self.create_by_input_uid()),
            MenuItem(title=_lang.menu.add_by_cookie, options=lambda: self.create_by_cookie()),
        ]
        uid_list = self.get_uid_list()
        menu_list.extend(
            [
                MenuItem(
                    title=_lang.menu.select_account.format(uid),
                    # lambda 闭包捕获外部变量值 uid = uid
                    options=lambda uid=uid: self.login(uid),
                )
                for uid in uid_list
            ]
        )
        return menu_list


def _input_uid():
    """输入并校验UID格式

    Returns:
        "0": exit
        str: uid
    """
    while True:
        uid = input(_lang.menu.input_uid).strip()
        if uid == "0":
            return None
        if not Account.verify_uid(uid):
            print(color_str(_lang.menu.invalid_uid_format, color="yellow"))
            continue
        return uid


def get_game_record_card(cookie: Cookie):
    param = {"uid": cookie.account_id}

    header = Header()
    header.update(DefaultHeader.PC_HEADER)
    header.set_ds("v2", Salt.X4, param)

    data = request(
        method="get",
        url=GAME_RECORD_CARD_URL.get_url(GameBiz.CN),
        headers=header.dict(),
        params=param,
        cookies=cookie.model_dump("all"),
    )
    logger.debug("get game record card")
    return UserGameRecordCards(**data)
