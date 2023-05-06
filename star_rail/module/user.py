import os
import re
from pathlib import Path
from typing import Optional

from star_rail import constant
from star_rail.exceptions import UserInfoError
from star_rail.utils.functional import (
    clear_screen,
    color_str,
    input_int,
    load_json,
    save_json,
    singleton,
)
from star_rail.utils.log import logger


class User:
    UID_RE = re.compile("^[1-9][0-9]{8}$")

    def __init__(self, uid: str, location: str = "", gacha_url: str = "") -> None:
        self.uid = uid
        self.location = location
        self.gacha_url = gacha_url
        self.profile_path = Path(constant.DATA_PATH, self.uid, f"UserProfile_{self.uid}.json")
        self.gacha_log_json_path = Path(constant.DATA_PATH, self.uid, f"GachaLog_{self.uid}.json")
        self.gacha_log_xlsx_path = Path(constant.DATA_PATH, self.uid, f"GachaLog_{self.uid}.xlsx")
        self.gacha_log_analyze_path = Path(constant.DATA_PATH, self.uid, f"Analyze_{self.uid}.json")
        self._init_location()

    @staticmethod
    def verify_uid(uid: str) -> bool:
        if not isinstance(uid, str):
            return False
        if None is User.UID_RE.fullmatch(uid):
            return False
        return True

    def _init_location(self):
        if "6" <= self.uid[0] <= "9":
            self.location = "global"
        elif "1" <= self.uid[0] <= "5":
            self.location = "cn"

    def to_dict(self):
        user_data = {}
        user_data["uid"] = self.uid
        user_data["gacha_url"] = self.gacha_url
        user_data["location"] = self.location
        return user_data

    def __str__(self):
        return str(self.to_dict())

    def save_profile(self):
        try:
            save_json(self.profile_path, self.to_dict())
        except Exception:
            raise UserInfoError("保存账号信息失败")

    def load_profile(self):
        try:
            local_user_info = load_json(self.profile_path)
        except Exception:
            raise UserInfoError("加载账号信息失败")
        if not User.verify_user_profile(local_user_info) or self.uid != local_user_info["uid"]:
            raise UserInfoError("加载账号信息出现数据错误")
        self.gacha_url = local_user_info["gacha_url"]
        self.location = local_user_info["location"]

    @staticmethod
    def verify_user_profile(user_profile: dict):
        if (
            "uid" not in user_profile
            or "gacha_url" not in user_profile
            or "location" not in user_profile
        ):
            return False
        return True


@singleton
class Account:
    def __init__(self, user: User = None) -> None:
        self.login_user = user


def add_by_uid(uid: str):
    if not User.verify_uid(uid):
        raise UserInfoError("UID 格式错误, UID : {}", uid)
    user = User(uid)
    user.save_profile()
    return user


def get_uid_list():
    """扫描目录查询可用的 userprofile 文件

    Returns:
        list(str): UID 列表
    """
    if not os.path.isdir(constant.DATA_PATH):
        return

    # folders named in the format of UID
    file_list = [
        name
        for name in os.listdir(constant.DATA_PATH)
        if os.path.isdir(os.path.join(constant.DATA_PATH, name)) and User.verify_uid(name)
    ]
    uid_list = []
    # load UserProfile.json
    for folder in file_list:
        path = Path(constant.DATA_PATH, folder, "UserProfile_{}.json".format(folder))
        if not path.exists():
            continue
        user_profile = load_json(path)
        if (
            not user_profile
            or ("uid" not in user_profile)
            or not User.verify_uid(user_profile["uid"])
        ):
            logger.error("文件 {} 加载出现错误，将跳过此文件", path)
            continue
        uid_list.append(user_profile["uid"])
    logger.debug("检测到 {} 的配置文件", uid_list)
    return uid_list


def choose_user_menu(create_user=True) -> Optional[User]:
    """用户选择菜单：可选择已有的用户或新建用户

    Args:
        create_user (bool, optional): 在菜单中是否显示新建用户选项. Defaults to True.

    Return:
        str: uid
    """
    DEFAULT_BANNER_LENGTH = 40
    uid_list = get_uid_list()
    length = len(uid_list)
    clear_screen()
    print("              选择账户UID")
    print("=" * DEFAULT_BANNER_LENGTH)
    for index in range(length):
        print("{}.{}".format(index + 1, uid_list[index]))
    if create_user:
        print("{}.{}".format(length + 1, "创建新用户"))
    print("")
    print("0.退出选择")
    print("=" * DEFAULT_BANNER_LENGTH)

    max_choose_range = length + 1 if create_user else length
    choose = input_int(0, max_choose_range)

    account = Account()
    if choose == 0:
        # 0 退出用户选择
        return ""
    elif choose == length + 1:
        uid = input_uid()
        if uid is None:
            return ""
        account.login_user = add_by_uid(uid)
    else:
        choose_user = uid_list[choose - 1]
        account.login_user = User(choose_user)
        account.login_user.load_profile()

    logger.success("设置账号 {}".format(account.login_user.uid))


def input_uid():
    """accept input and verify uid

    Returns:
        "0": exit
        str: uid
    """
    while True:
        uid = input("请输入用户UID, 输入 0 取消新建用户\n")
        if uid == "0":
            return None
        if not User.verify_uid(uid):
            print(color_str("请输入正确格式的UID", "red"))
            continue
        return uid


def get_account_status():
    account = Account()
    if None is account.login_user:
        return "当前未设置账号"
    else:
        return "当前账号 {}".format(color_str(account.login_user.uid, "green"))
