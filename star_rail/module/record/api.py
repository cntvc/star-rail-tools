import os
import re
import subprocess
import tempfile
import typing

import yarl

from ...utils.log import logger
from ..game_client import GameClient
from ..mihoyo.account import Account, GameBiz
from ..mihoyo.routes import GACHA_LOG_URL


def get_from_user_cache(user: Account):
    logger.debug("从用户缓存获取抽卡链接")
    if not user.gacha_url:
        return None
    return yarl.URL(user.gacha_url)


def get_from_game_cache(user: Account):
    logger.debug("从游戏缓存获取抽卡链接")

    tmp_file_path = os.path.join(tempfile.gettempdir(), "data_2")
    webcache_path = GameClient(user).get_webcache_path()
    _copy_file_with_powershell(webcache_path, tmp_file_path)

    logger.debug("开始读取缓存")
    with open(tmp_file_path, "rb") as file:
        results = file.read().split(b"1/0/")
    os.remove(tmp_file_path)

    url = None
    # reverse order traversal
    for result in results[::-1]:
        result = result.decode(errors="ignore")
        text = _match_api(result)
        if text:
            url = text
            break

    if not url:
        return None
    url = _replace_host_path(url)
    return yarl.URL(url)


def _copy_file_with_powershell(source_path, destination_path):
    powershell_command = f"Copy-Item '{source_path}' '{destination_path}'"

    try:
        subprocess.run(["powershell", powershell_command], check=True)
        logger.debug("缓存文件拷贝完成")
    except subprocess.CalledProcessError:
        logger.error("缓存文件读取失败")
        return False
    return destination_path


def get_from_clipboard():
    logger.debug("从剪切板获取抽卡链接")
    import pyperclip

    text = pyperclip.paste()
    url = _match_api(text)
    if not url:
        return None
    url = _replace_host_path(url)
    return yarl.URL(url)


GACHA_LOG_API_RE = re.compile(
    "https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)"
)


def _match_api(api: typing.Optional[str]):
    """从字符串匹配抽卡链接"""
    if not api:
        return None
    res = GACHA_LOG_API_RE.search(api)
    return res.group() if res else None


def _replace_host_path(url: str):
    """替换链接的 host 路径"""
    if not url:
        raise ValueError("Invalid url value: ", url)
    spliturl = url.split("?")
    if "webstatic-sea.hoyoverse.com" in spliturl[0] or "api-os-takumi" in spliturl[0]:
        spliturl[0] = GACHA_LOG_URL.get_url(GameBiz.GLOBAL)
    else:
        spliturl[0] = GACHA_LOG_URL.get_url(GameBiz.CN)
    url = "?".join(spliturl)
    return url
