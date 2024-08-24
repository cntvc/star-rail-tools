from __future__ import annotations

import os
import re
import subprocess
import typing

import yarl

from star_rail import constants
from star_rail.module.game_client import GameClient
from star_rail.utils.logger import logger

if typing.TYPE_CHECKING:
    from star_rail.module import Account

__all__ = ["GachaUrlProvider"]


_GACHA_RECORD_URL_RE = re.compile(
    r"https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)"
)


class GachaUrlProvider:
    def _match_api(self, api: str | None) -> str | None:
        """从字符串匹配抽卡链接"""
        if not api:
            return None
        match = _GACHA_RECORD_URL_RE.search(api)
        return match.group() if match else None

    def _copy_file_with_powershell(self, source_path, destination_path):
        powershell_command = f"Copy-Item '{source_path}' '{destination_path}'"

        subprocess.run(["powershell", powershell_command], check=True)

        return destination_path

    def parse_game_web_cache(self, user: Account):
        logger.debug("Parse game client web cache.")
        tmp_file_path = os.path.join(constants.TEMP_PATH, "data_2")
        webcache_path = GameClient(user).get_webcache_path()
        self._copy_file_with_powershell(webcache_path, tmp_file_path)

        with open(tmp_file_path, "rb") as file:
            results = file.read().split(b"1/0/")
        os.remove(tmp_file_path)

        url = None

        for result in results[::-1]:
            result = result.decode(errors="ignore")
            text = self._match_api(result)
            if text:
                url = text
                break

        if not url:
            return None
        return yarl.URL(url)

    def parse_clipboard_url(self):
        logger.debug("Parse clipboard.")
        import pyperclip

        text = pyperclip.paste()
        url = self._match_api(text)
        if not url:
            return None
        return yarl.URL(url)
