import abc
import enum
import os
import re
import tempfile
from typing import Callable, Dict, Optional

import win32api

from star_rail.module.account import Account, GameBizType
from star_rail.module.game_client import GameClient
from star_rail.module.routes import GACHA_LOG_URL
from star_rail.utils import clipboard
from star_rail.utils.log import logger

__all__ = ["ProviderType", "get_provider"]


class GachaUrlProvider(abc.ABC):
    @abc.abstractmethod
    def get_url(self):
        pass


class UserCacheProvider(GachaUrlProvider):
    def __init__(self, user: Account) -> None:
        self.user = user

    def get_url(self):
        logger.debug("从用户缓存获取抽卡链接")
        if not self.user or self.user.gacha_url:
            logger.warning("从用户数据未读取到抽卡链接")
            return None
        return self.user.gacha_url


class GameWebCacheProvider(GachaUrlProvider):
    def __init__(self, user: Account) -> None:
        self.user = user

    def get_url(self):
        logger.debug("从游戏缓存获取抽卡链接")

        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name
        webcache_path = GameClient(self.user).get_webcache_path()
        if not webcache_path:
            return None
        win32api.CopyFile(webcache_path, tmp_file_name)

        logger.debug("开始读取缓存")
        with open(tmp_file_name, "rb") as file:
            results = file.read().split(b"1/0/")
        os.remove(tmp_file_name)

        url = None
        # reverse order traversal
        for result in results[::-1]:
            result = result.decode(errors="ignore")
            text = match_gacha_log_api(result)
            if text:
                url = text
                break

        if not url:
            logger.warning("从游戏缓存文件中未找到抽卡链接，请到游戏内查看抽卡记录后重试")
            return None
        url = replace_gacha_log_url_host_path(url)
        return url


class ClipboardProvider(GachaUrlProvider):
    def get_url(self):
        import html

        logger.debug("从剪切板获取抽卡链接")
        text = clipboard.get_text_or_html()
        text = html.unescape(text)
        url = match_gacha_log_api(text)
        if not url:
            logger.warning("从剪切板未读取到抽卡链接")
            return None
        url = replace_gacha_log_url_host_path(url)
        return url


GACHA_LOG_API_RE = re.compile(
    "https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)"
)


def match_gacha_log_api(api: Optional[str]):
    if not api:
        return None
    res = GACHA_LOG_API_RE.search(api)
    return res.group() if res else None


def replace_gacha_log_url_host_path(url: str):
    """Replace the host in the link to generate the gacha log API."""
    if not url:
        raise ValueError("Invalid url value: ", url)
    spliturl = url.split("?")
    if "webstatic-sea.hoyoverse.com" in spliturl[0] or "api-os-takumi" in spliturl[0]:
        spliturl[0] = GACHA_LOG_URL.get_url(GameBizType.GLOBAL)
    else:
        spliturl[0] = GACHA_LOG_URL.get_url(GameBizType.CN)
    url = "?".join(spliturl)
    return url


class ProviderType(enum.Enum):
    USER_PROFILE = 1
    WEB_CACHE = 2
    CLIPBOARD = 3


def get_provider(type: ProviderType, user: Optional[Account] = None):
    _provider_type: Dict[ProviderType, Callable[[], GachaUrlProvider]] = {
        ProviderType.USER_PROFILE: lambda: UserCacheProvider(user),
        ProviderType.WEB_CACHE: lambda: GameWebCacheProvider(user),
        ProviderType.CLIPBOARD: lambda: ClipboardProvider(),
    }
    return _provider_type[type]
