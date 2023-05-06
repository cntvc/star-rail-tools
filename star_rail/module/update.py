"""update"""
import json
import traceback

import requests
from requests import RequestException, Timeout

from star_rail import __version__ as version
from star_rail import constant
from star_rail.utils.functional import clear_screen, color_str
from star_rail.utils.log import logger

GITHUB_RELEASE_API = "https://api.github.com/repos/cntvc/star-rail-tools/releases/latest"

GITHUB_RELEASE_URL = "https://github.com/cntvc/star-rail-wish-tools/releases/latest"


def get_latest_tag(url: str):
    """
    get latest release info

    Returns:
        str: tag_name
    """
    response = requests.get(url, timeout=constant.TIMEOUT).content.decode("utf-8")
    data = json.loads(response)
    if "tag_name" not in data:
        return ""
    return data["tag_name"]


def check_update():
    """
    check app is need update
    """
    print("正在检测软件更新...")
    try:
        tag = get_latest_tag(GITHUB_RELEASE_API)
    except (Timeout, RequestException):
        print(color_str("检测更新失败, 请检查网络连接状态", "red"))
        logger.debug(traceback.format_exc())
        return False

    if not tag:
        logger.warning("检测更新失败，未获取到版本信息\n")
        return False
    if tag != version:
        clear_screen()
        logger.warning("检测到新版本 v{} -> v{} 可前往官网下载最新版本", version, tag)
        print(GITHUB_RELEASE_URL)
        return True
    else:
        logger.success("当前已是最新版本\n")
        return True
