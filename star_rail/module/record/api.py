"""跃迁记录 API 来源"""
import os
import re
import subprocess
from typing import Optional

import yarl

from star_rail import constants
from star_rail import exceptions as error
from star_rail.module import Account, routes, types
from star_rail.module.game_client import GameClient
from star_rail.utils import functional
from star_rail.utils.log import logger

__all__ = ["get_game_cache_url", "get_clipboard_url"]


GACHA_RECORD_URL_RE = re.compile(
    r"https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)"
)


def _match_api(api: Optional[str]) -> Optional[str]:
    """从字符串匹配抽卡链接"""
    if not api:
        return None
    match = GACHA_RECORD_URL_RE.search(api)
    return match.group() if match else None


def _replace_url_path(url: str):
    base_url = str(routes.GACHA_LOG_URL.get_url(types.GameBiz.CN))
    split_url = url.split("?")
    if "webstatic-sea.hoyoverse.com" in split_url[0] or "api-os-takumi" in split_url[0]:
        base_url = str(routes.GACHA_LOG_URL.get_url(types.GameBiz.GLOBAL))

    split_url[0] = base_url
    return "?".join(split_url)


def _copy_file_with_powershell(source_path, destination_path):
    powershell_command = f"Copy-Item '{source_path}' '{destination_path}'"

    try:
        subprocess.run(["powershell", powershell_command], check=True)
    except subprocess.CalledProcessError:
        raise error.HsrException("Copy cache file failed")

    return destination_path


def get_game_cache_url(user: Account) -> Optional[yarl.URL]:
    """获取游戏 Web 缓存中跃迁记录链接"""
    logger.debug("get url from game web cache")
    tmp_file_path = os.path.join(constants.TEMP_PATH, "data_2")
    webcache_path = GameClient(user).get_webcache_path()
    _copy_file_with_powershell(webcache_path, tmp_file_path)

    with open(tmp_file_path, "rb") as file:
        results = file.read().split(b"1/0/")
    os.remove(tmp_file_path)

    url = None

    for result in results[::-1]:
        result = result.decode(errors="ignore")
        text = _match_api(result)
        if text:
            url = text
            break

    if not url:
        return None
    url = _replace_url_path(url)
    return yarl.URL(url)


def get_clipboard_url() -> Optional[yarl.URL]:
    """获取剪切板中跃迁记录链接"""
    logger.debug("get url from clipboard")
    import pyperclip

    text = pyperclip.paste()
    logger.debug(functional.desensitize_url(text, "authkey"))
    url = _match_api(text)
    if not url:
        return None
    url = _replace_url_path(url)
    return yarl.URL(url)
