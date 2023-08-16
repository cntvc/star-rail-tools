import re
from pathlib import Path
from typing import Union

import pyperclip
from pydantic import BaseModel, ValidationError, field_validator, model_validator

from star_rail import constants
from star_rail.config import settings
from star_rail.core import DBClient
from star_rail.exceptions import ParamTypeError, exec_catch
from star_rail.i18n import i18n
from star_rail.utils.functional import Singleton, color_str
from star_rail.utils.log import logger
from star_rail.utils.menu import MenuItem

from .api_client import PC_HEADER, Header, Salt, request
from .cookie import Cookie
from .mapper import CookieMapper, UserMapper
from .model import GameRecordCard, UserGameRecordCards
from .routes import GAME_RECORD_CARD_URL
from .types import GameBiz, GameType, Region

_UID_RE = re.compile("^[1-9][0-9]{8}$")

_lang = i18n.account


__all__ = [
    "verify_uid_format",
    "Account",
    "AccountManager",
]


def verify_uid_format(v):
    if Account.verify_uid(v):
        return v
    raise ValidationError(f"Invalid uid format: {v}")


class Account(BaseModel):
    uid: str  # 星铁账户
    cookie: Cookie = Cookie()
    gacha_url: str = ""

    # 以下成员根据 uid 初始化
    region: str = ""
    game_biz: str = ""

    gacha_log_xlsx_path: Path = ""
    gacha_log_analyze_path: Path = ""
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
        self.gacha_log_xlsx_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_{self.uid}.xlsx")
        self.gacha_log_analyze_path = Path(constants.TEMP_PATH, f"GachaAnalyze_{self.uid}.json")
        self.srgf_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_SRGF_{self.uid}.json")

    def _init_game_biz(self):
        self.game_biz = GameBiz.get_by_uid(self.uid).value

    def _init_region(self):
        self.region = Region.get_by_uid(self.uid).value

    def save_profile(self):
        from ..mihoyo import converter

        """保存到 user 表和 cookie 表"""
        user_mapper = converter.user_to_mapper(self)
        with DBClient() as db:
            db.insert(user_mapper, "update")
            db.insert(converter.user_to_cookie_mapper(self), "update")

    def reload_profile(self):
        """重新加载用户数据

        Return:
            失败: None
            成功: True
        """
        from ..mihoyo import converter

        user_mapper = UserMapper.query_user(self.uid)
        if user_mapper is None:
            return

        local_user = converter.user_mapper_to_user(user_mapper)
        user_ck = CookieMapper.query_cookie(self.uid)
        if user_ck:
            local_cookie = converter.cookie_mapper_to_cookie(user_ck)
            local_user.cookie = local_cookie

        for k in local_user.model_fields_set:
            if k not in self._serialize_include_keys:
                continue
            v = getattr(local_user, k)
            setattr(self, k, v)

        return True

    def model_dump(self):
        return super().model_dump(include=self._serialize_include_keys)

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and _UID_RE.fullmatch(v) is not None


@Singleton()
class AccountManager:
    def __init__(self) -> None:
        if not settings.DEFAULT_UID:
            self.user = None
            return
        self.user = Account(settings.DEFAULT_UID)
        result = self.user.reload_profile()
        if not result:
            # 本地文件设置了默认账户数据库却不存在该账号
            self.user = None
            settings.DEFAULT_UID = ""
            settings.save()

    def login(self, user: Union[str, Account]):
        if isinstance(user, str):
            self.user = Account(user)
        elif isinstance(user, Account):
            self.user = user
        else:
            raise ParamTypeError(i18n.error.param_type_error, type(user))

        self.user.reload_profile()
        logger.success(_lang.login_account_success, self.user.uid)
        settings.DEFAULT_UID = self.user.uid
        settings.save()

    def create_by_input_uid(self):
        uid = _input_uid()
        if uid is None:
            return
        user = Account(uid)
        if not user.reload_profile():
            # 如果库里没有该账户，则创建
            user.save_profile()
        logger.success(_lang.add_account_success, user.uid)

    @exec_catch(level="warning")
    def create_by_cookie(self):
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)
        if cookie is None:
            logger.warning(_lang.invalid_cookie)
            return
        if cookie.verify_login_ticket() and not cookie.verify_stoken():
            cookie.refresh_stoken_by_login_ticket()
            cookie.refresh_cookie_token_by_stoken()
        roles = get_game_record_card(cookie)
        for role in roles.list:
            if not self.is_hsr_role(role):
                continue

            user = Account(uid=role.game_role_id)
            # 尝试加载本地数据后，更新 cookie 并保存
            user.reload_profile()
            user.cookie = cookie
            user.save_profile()

            # 如果与当前登陆的账号一致，直接更新数据
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

    def get_status_desc(self):
        if self.user is not None:
            return _lang.current_account.format(color_str(self.user.uid, color="green"))
        return _lang.without_account

    def gen_account_menu(self):
        uid_list = self.get_uid_list()
        menu_list = [
            # lambda 闭包捕获外部变量值 uid = uid
            MenuItem(
                title=_lang.menu.select_account.format(uid), options=lambda uid=uid: self.login(uid)
            )
            for uid in uid_list
        ]
        menu_list.append(
            MenuItem(title=_lang.menu.add_by_game_uid, options=lambda: self.create_by_input_uid())
        )
        menu_list.append(
            MenuItem(title=_lang.menu.add_by_cookie, options=lambda: self.create_by_cookie())
        )
        return menu_list


def _input_uid():
    """输入并校验UID格式

    Returns:
        "0": exit
        str: uid
    """
    while True:
        uid = input(_lang.menu.input_uid)
        if uid == "0":
            return None
        if not Account.verify_uid(uid):
            print(color_str(_lang.menu.invalid_uid_format, color="yellow"))
            continue
        return uid


def get_game_record_card(cookie: Cookie):
    param = {"uid": cookie.account_id}

    header = Header()
    header.update(PC_HEADER)
    header.set_ds("v2", Salt.X4, param)

    data = request(
        method="get",
        url=GAME_RECORD_CARD_URL.get_url(GameBiz.CN),
        headers=header.dict(),
        params=param,
        cookies=cookie.model_dump("app"),
    )
    logger.debug("get game record card")
    return UserGameRecordCards(**data)
