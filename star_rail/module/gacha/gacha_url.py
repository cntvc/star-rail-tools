import abc
import enum
import os
import re
import subprocess
import tempfile
from typing import Callable, Dict, Optional

from star_rail.i18n import i18n
from star_rail.module.game_client import GameClient
from star_rail.module.mihoyo.account import Account
from star_rail.module.mihoyo.routes import GACHA_LOG_URL
from star_rail.module.mihoyo.types import GameBiz
from star_rail.utils.log import logger

__all__ = ["ProviderType", "get_provider"]

_lang = i18n.gacha_url


class GachaUrlProvider(abc.ABC):
    @abc.abstractmethod
    def get_url(self):
        pass


class UserCacheProvider(GachaUrlProvider):
    def __init__(self, user: Account) -> None:
        self.user = user

    def get_url(self):
        logger.debug("从用户缓存获取抽卡链接")
        if not self.user.gacha_url:
            logger.warning(_lang.unfind_link)
            return None
        return self.user.gacha_url


class GameWebCacheProvider(GachaUrlProvider):
    def __init__(self, user: Account) -> None:
        self.user = user

    def copy_file_with_powershell(self, source_path, destination_path):
        powershell_command = f"Copy-Item '{source_path}' '{destination_path}'"

        try:
            subprocess.run(["powershell", powershell_command], check=True)
            logger.debug("缓存文件拷贝完成")
        except subprocess.CalledProcessError:
            logger.error("缓存文件读取失败")
            return False
        return destination_path

    def get_url(self):
        logger.debug("从游戏缓存获取抽卡链接")

        tmp_file_path = os.path.join(tempfile.gettempdir(), "data_2")
        webcache_path = GameClient(self.user).get_webcache_path()
        if not webcache_path:
            return None
        self.copy_file_with_powershell(webcache_path, tmp_file_path)

        logger.debug("开始读取缓存")
        with open(tmp_file_path, "rb") as file:
            results = file.read().split(b"1/0/")
        os.remove(tmp_file_path)

        url = None
        # reverse order traversal
        for result in results[::-1]:
            result = result.decode(errors="ignore")
            text = match_gacha_log_api(result)
            if text:
                url = text
                break

        if not url:
            logger.warning(_lang.unfind_link)
            return None
        url = replace_gacha_log_url_host_path(url)
        return url


class ClipboardProvider(GachaUrlProvider):
    def get_url(self):
        logger.debug("从剪切板获取抽卡链接")
        import pyperclip

        text = pyperclip.paste()
        url = match_gacha_log_api(text)
        if not url:
            logger.warning(_lang.unfind_link)
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
        spliturl[0] = GACHA_LOG_URL.get_url(GameBiz.GLOBAL)
    else:
        spliturl[0] = GACHA_LOG_URL.get_url(GameBiz.CN)
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
