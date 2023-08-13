import os
import re
from pathlib import Path
from typing import List, Union

import pyperclip
from pydantic import BaseModel, ValidationError, model_validator, validator

from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.utils.functional import color_str, load_json, save_json
from star_rail.utils.log import logger
from star_rail.utils.menu import MenuItem

from .api_client import PC_HEADER, Header, Salt, request
from .cookie import Cookie
from .model import GameRecordCard, UserGameRecordCards
from .routes import GAME_RECORD_CARD_URL
from .types import GameBiz, GameType, Region

_UID_RE = re.compile("^[1-9][0-9]{8}$")

_lang = i18n.account


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

    profile_path: Path = ""
    gacha_log_json_path: Path = ""
    gacha_log_xlsx_path: Path = ""
    gacha_log_analyze_path: Path = ""
    srgf_path: Path = ""

    def __init__(self, uid: str, **data):
        super().__init__(uid=uid, **data)

    _verify_uid_format = validator("uid", always=True)(verify_uid_format)

    _serialize_include_keys = {"cookie", "uid", "gacha_url"}

    @model_validator(mode="after")
    def init_param(self):
        self._init_datafile_path()
        self._init_game_biz()
        self._init_region()

    def _init_datafile_path(self):
        self.profile_path = Path(constants.ROOT_PATH, self.uid, f"UserProfile_{self.uid}.json")
        self.gacha_log_json_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_{self.uid}.json")
        self.gacha_log_xlsx_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_{self.uid}.xlsx")
        self.gacha_log_analyze_path = Path(
            constants.ROOT_PATH, self.uid, f"GachaAnalyze_{self.uid}.json"
        )
        self.srgf_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_SRGF_{self.uid}.json")

    def _init_game_biz(self):
        self.game_biz = GameBiz.get_by_uid(self.uid).value

    def _init_region(self):
        self.region = Region.get_by_uid(self.uid).value

    def save_profile(self):
        save_json(self.profile_path, self.model_dump())

    def load_profile(self):
        if not os.path.exists(self.profile_path):
            return False
        local_profile = load_json(self.profile_path)
        local_user_model = Account(**local_profile)
        for k in local_user_model.model_fields_set:
            if k not in self._serialize_include_keys:
                continue
            v = getattr(local_user_model, k)
            setattr(self, k, v)

        self._init_game_biz()
        self._init_datafile_path()
        return True

    def model_dump(self):
        return super().model_dump(include=self._serialize_include_keys)

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and _UID_RE.fullmatch(v) is not None


class AccountManager:
    # TODO 重构
    def __init__(self) -> None:
        if not settings.DEFAULT_UID:
            self._account = None
            return
        self._account = Account(settings.DEFAULT_UID)
        result = self._account.load_profile()
        if not result:
            # 不存在该账号的文件
            self._account = None
            settings.DEFAULT_UID = ""
            settings.save()

    @property
    def account(self):
        return self._account

    def login(self, v: Union[str, Account]):
        if isinstance(v, str):
            self._account = Account(v)
            self._account.load_profile()
        elif isinstance(v, Account):
            self._account = v
        else:
            raise ValueError("登陆账户数据错误")
        logger.debug("设置账户：{}", self.account.uid)
        settings.DEFAULT_UID = self.account.uid
        settings.save()

    def get_status_desc(self):
        if self._account is not None:
            return _lang.account_uid.format(color_str(self._account.uid, color="green"))
        return _lang.without_account


class AccountMenu:
    def __init__(self) -> None:
        self._menu_list: List[MenuItem] = []

    def create(self):
        uid_list = self._get_uids()
        self._menu_list = [
            # lambda 闭包捕获外部变量值 uid = uid
            MenuItem(title=f"{uid}", options=lambda uid=uid: account_manager.login(uid))
            for uid in uid_list
        ]
        self._menu_list.append(
            MenuItem(title="输入游戏UID", options=lambda: self._create_account_by_input())
        )
        self._menu_list.append(
            MenuItem(title="通过cookie添加账号", options=lambda: self._create_account_by_cookie())
        )
        return self._menu_list

    def _get_uids(self):
        """扫描目录查询可用的 userprofile 文件

        Returns:
            list(str): UID 列表
        """
        if not os.path.isdir(constants.ROOT_PATH):
            return

        # folders named in the format of UID
        file_list = [
            name
            for name in os.listdir(constants.ROOT_PATH)
            if os.path.isdir(os.path.join(constants.ROOT_PATH, name)) and Account.verify_uid(name)
        ]
        uid_list = []
        for uid in file_list:
            path = Path(constants.ROOT_PATH, uid, "UserProfile_{}.json".format(uid))
            if not path.exists():
                continue
            uid_list.append(uid)
        logger.debug("检测到 {} 的配置文件", uid_list)
        return uid_list

    def _input_uid(self):
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

    def _create_account_by_input(self):
        uid = self._input_uid()
        if uid is None:
            return ""
        user = Account(uid)
        user.save_profile()
        logger.debug("添加账号:{}", uid)
        account_manager.login(user)

    def _create_account_by_cookie(self):
        cookie_str = pyperclip.paste()
        cookie = Cookie.parse(cookie_str)
        if cookie is None:
            logger.warning("未识别到有效的cookie")
            return
        if cookie.verify_login_ticket() and not cookie.verify_stoken():
            cookie.refresh_stoken_by_login_ticket()
            cookie.refresh_cookie_token_by_stoken()
        roles = get_game_record_card(cookie)
        for role in roles.list:
            if not is_hsr_role(role):
                continue

            user = Account(uid=role.game_role_id)
            # 尝试加载本地数据后，更新 cookie 并保存
            user.load_profile()
            user.cookie = cookie
            user.save_profile()


def is_hsr_role(role: GameRecordCard):
    """是否为星穹铁道账户"""
    return role.game_id == GameType.STAR_RAIL.value


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
    return UserGameRecordCards(**data)


# TODO stoken刷新其他cookie的接口

account_manager = AccountManager()
