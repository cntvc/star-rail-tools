import os
import re
import subprocess
import typing

import yarl
from loguru import logger

from star_rail import constants
from star_rail.module.base import BaseClient
from star_rail.module.game_client import GameClient

if typing.TYPE_CHECKING:
    pass

_GACHA_RECORD_URL_RE = re.compile(
    r"https://.+?&auth_appid=webview_gacha&.+?authkey=.+?&game_biz=hkrpg_(?:cn|global)"
)

__all__ = ["GachaUrl"]


class GachaUrl(BaseClient):
    @staticmethod
    def _match_api(api: str) -> str | None:
        if not api:
            return None
        match = _GACHA_RECORD_URL_RE.search(api)
        return match.group() if match else None

    def _copy_file_with_powershell(self, source_path, destination_path):
        powershell_command = f"Copy-Item '{source_path}' '{destination_path}'"

        subprocess.run(["powershell", powershell_command], check=True)

        return destination_path

    def parse_from_web_cache(self):
        logger.debug("Parse game client web cache")
        tmp_file_path = os.path.join(constants.TEMP_PATH, "data_2")
        web_cache_path = GameClient(self.user).get_web_cache_path()
        self._copy_file_with_powershell(web_cache_path, tmp_file_path)

        with open(tmp_file_path, "rb") as file:
            results = file.read().split(b"1/0/")
        os.remove(tmp_file_path)

        for result in results[::-1]:
            result = result.decode(errors="ignore")
            if url := self._match_api(result):
                return yarl.URL(url)
        return None

    @staticmethod
    def verify_url(url: str):
        if res := GachaUrl._match_api(url):
            return yarl.URL(res)
        return None
