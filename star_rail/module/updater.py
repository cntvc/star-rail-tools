"""updater"""

import json
import os
import re
import shutil
import tempfile
from typing import Tuple

import requests
from requests import RequestException, Timeout
from tqdm import tqdm

from star_rail import __version__ as version
from star_rail import constant, get_exe_name
from star_rail.utils.functional import color_str
from star_rail.utils.log import logger


def input_yes_or_no(prompt: str = "", default="y"):
    """输入 y/N 并校验"""
    while True:
        user_input = input(prompt).strip().lower()
        if not user_input:
            return default
        elif user_input == "y" or user_input == "n":
            return user_input
        else:
            print(color_str("请输入有效的选项，只能输入 'y' 或 'N'。", "red"))


def download_file(url: str, file_path: str = ""):
    _DEFAULT_CHUNK_SIZE = 1024
    if not file_path:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        file_path = temp_file.name
    with open(file_path, "wb") as f:
        with requests.get(url, stream=True, timeout=constant.TIMEOUT) as r:
            file_size = int(r.headers.get("content-length", 0))
            with tqdm(total=file_size, unit="B", unit_scale=True, desc="StarRailTools") as pbar:
                for chunk in r.iter_content(chunk_size=_DEFAULT_CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        pbar.update(_DEFAULT_CHUNK_SIZE)
    return file_path


def check_update() -> Tuple[bool, dict]:
    """
    Return:
        False：更新出现错误
        True and {}: 无需更新
    """
    print("正在检测软件更新...")
    GITHUB_RELEASE_API = "https://api.github.com/repos/cntvc/star-rail-tools/releases/latest"
    try:
        response = requests.get(GITHUB_RELEASE_API, timeout=constant.TIMEOUT).content.decode(
            "utf-8"
        )
        data = json.loads(response)
    except (Timeout, RequestException) as e:
        print(color_str("检测更新失败, 请检查网络连接状态", "red"))
        logger.debug(e)
        return False, {}
    if "tag_name" not in data:
        logger.error("检测更新失败，未获取到版本信息")
        return False, {}

    tag_name = data["tag_name"]
    if tag_name == version:
        return True, {}

    logger.warning("检测到新版本 v{} -> v{}", version, tag_name)
    return True, data


def update():
    res, data = check_update()
    if not res:
        return False
    if not data:
        return True
    user_input = input_yes_or_no("请输入（y/N）以选择是否进行更新（默认 y）")
    if user_input == "n":
        return True

    origin_url = data["assets"][0]["browser_download_url"]
    latest_version_exe_name = data["assets"][0]["name"]
    try:
        temp_file = download_file(origin_url)
    except (Timeout, RequestException) as e:
        print(color_str("下载新版本文件失败, 请检查网络连接状态", "red"))
        logger.debug(e)
        return False
    logger.debug("新版本程序临时文件：{}", temp_file)
    latest_version_exe_path = os.path.join(os.getcwd(), latest_version_exe_name)
    shutil.move(temp_file, latest_version_exe_path)
    update_and_restart(latest_version_exe_name, get_exe_name())


def get_cur_version_info():
    GITHUB_TAG_API = "https://api.github.com/repos/cntvc/star-rail-tools/releases/tags/{}".format(
        version
    )
    try:
        response = requests.get(GITHUB_TAG_API, timeout=constant.TIMEOUT).content.decode("utf-8")
        data = json.loads(response)
    except (Timeout, RequestException) as e:
        print(color_str("查询版本信息失败, 请检查网络连接状态", "red"))
        logger.debug(e)
        return {}
    return data


def parse_changelog(release_data):
    """移除更新日志中的链接等信息"""
    changelog_raw = release_data["body"]
    link_pattern = r"\[[^\]]+\]\([^)]+\)|https://[^ \n]+|\*\*Full Changelog[^ \n]+"
    change_log = re.sub(link_pattern, "", changelog_raw)
    return change_log.strip()


def update_and_restart(new_exe_name, old_exe_name):
    """启动新版本程序，通过传参清理旧版本文件"""
    logger.debug("launch app: {}\told app: {}", new_exe_name, old_exe_name)
    os.execv(new_exe_name, [new_exe_name, "--clean={}".format(old_exe_name), "--update-info"])
