import enum
import os
import re
from pathlib import Path
from typing import Union

from pydantic import BaseModel, Field, validator

from star_rail import constants
from star_rail.config import settings
from star_rail.i18n import i18n
from star_rail.utils.functional import color_str, load_json, save_json
from star_rail.utils.log import logger

UID_RE = re.compile("^[1-9][0-9]{8}$")

_lang = i18n.account


class GameBizType(str, enum.Enum):
    GLOBAL = "hkrpg_global"
    CN = "hkrpg_cn"

    @staticmethod
    def get_by_uid(uid):
        if "6" <= uid[0] <= "9":
            return GameBizType.GLOBAL
        elif "1" <= uid[0] <= "5":
            return GameBizType.CN
        else:
            raise ValueError(f"Invalid UID value: {uid}")


class RegionType(str, enum.Enum):
    """Game server region"""

    CN = "prod_gf_cn"
    ASIA = "prod_official_asia"
    USA = "prod_official_usa"
    EUR = "prod_official_eur"
    CHT = "prod_official_cht"

    @staticmethod
    def get_by_uid(uid: str):
        _region_dict = {
            "1": RegionType.CN,
            "2": RegionType.CN,
            "6": RegionType.USA,
            "7": RegionType.EUR,
            "8": RegionType.ASIA,
            "9": RegionType.CHT,
        }
        return _region_dict.get(uid[0], RegionType.CN)


def verify_game_biz(game_biz: str):
    # allow None value
    if not game_biz:
        return game_biz
    if any(game_biz == member.value for member in GameBizType):
        return game_biz
    raise ValueError(f"Invalid game_biz value: {game_biz}")


def verify_region(region):
    # allow None value
    if not region:
        return region
    if any(region == member.value for member in RegionType):
        return region
    raise ValueError(f"Invalid region value: {region}")


class Account(BaseModel):
    """米游社账户
    TODO 支持 cookie
    """

    mihoyo_uid: str = ""  # 米游社账户
    uid: str  # 星铁账户
    region: str = ""
    game_biz: str = ""
    gacha_url: str = ""
    # 路径在 init 中初始化
    profile_path: Path = Field(default="", exclude=True)
    gacha_log_json_path: Path = Field(default="", exclude=True)
    gacha_log_xlsx_path: Path = Field(default="", exclude=True)
    gacha_log_analyze_path: Path = Field(default="", exclude=True)
    srgf_path: Path = Field(default="", exclude=True)

    @validator("uid")
    def _uid_format(cls, v):
        if Account.verify_uid(v):
            return v
        raise ValueError(f"Invalid uid format: {v}")

    _verify_game_biz = validator("game_biz", always=True)(verify_game_biz)
    _verify_region = validator("region", always=True)(verify_region)

    def __init__(self, uid: str, **data):
        super().__init__(uid=uid, **data)
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
        self.srgf_path = Path(constants.ROOT_PATH, self.uid, f"GachaLog_srgf_{self.uid}.json")

    def _init_region(self):
        self.region = RegionType.get_by_uid(self.uid).value

    def _init_game_biz(self):
        self.game_biz = GameBizType.get_by_uid(self.uid).value

    def save_profile(self):
        save_json(self.profile_path, self.dict())

    def load_profile(self):
        if not os.path.exists(self.profile_path):
            return False

        local_profile = load_json(self.profile_path)
        for k, v in local_profile.items():
            if k in self.__fields__:
                setattr(self, k, v)

        self._init_game_biz()
        self._init_datafile_path()
        return True

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and UID_RE.fullmatch(v) is not None


class AccountManager:
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

    def get_status(self):
        return self._account is not None

    def get_status_msg(self):
        if self.get_status():
            return _lang.account_uid.format(color_str(self._account.uid, color="green"))
        return _lang.without_account


def get_uids():
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
    # load UserProfile.json
    for uid in file_list:
        path = Path(constants.ROOT_PATH, uid, "UserProfile_{}.json".format(uid))
        if not path.exists():
            continue
        uid_list.append(uid)
    logger.debug("检测到 {} 的配置文件", uid_list)
    return uid_list


def gen_account_manu(create_option: bool = False):
    """生成账户菜单

    Args:
        create_option (bool, optional): 是否添加创建新用户选项. Defaults to False.

    Returns:
        List[MenuItem]: 选项列表
    """
    from star_rail.utils.menu import MenuItem

    uid_list = get_uids()
    user_menu_list = [
        # lambda 闭包捕获外部变量值 uid = uid
        MenuItem(title=f"{uid}", options=lambda uid=uid: account_manager.login(uid))
        for uid in uid_list
    ]
    if create_option:
        user_menu_list.append(
            MenuItem(title=_lang.menu.creat_user, options=lambda: create_account_by_input())
        )
    return user_menu_list


def input_uid():
    """accept input and verify uid

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


def add_by_uid(uid: str):
    user = Account(uid=uid)
    user.save_profile()
    logger.debug("添加账号:{}", uid)
    return user


def create_account_by_input():
    uid = input_uid()
    if uid is None:
        return ""
    account_manager.login(add_by_uid(uid))


account_manager = AccountManager()
