import enum
import glob
import os
import re
from pathlib import Path

from star_rail.i18n import i18n
from star_rail.module.mihoyo.account import Account
from star_rail.module.mihoyo.types import GameBiz
from star_rail.utils.log import logger

_lang = i18n.game_client

MHY_LOG_ROOT_PATH = os.path.join(os.getenv("USERPROFILE"), "AppData", "LocalLow")


class GameLogPath(str, enum.Enum):
    CN = "miHoYo/崩坏：星穹铁道/"
    GLOBAL = "Cognosphere/Star Rail/"

    @staticmethod
    def get_by_user(user: Account):
        if user.game_biz == GameBiz.CN.value:
            return Path(MHY_LOG_ROOT_PATH, GameLogPath.CN.value, "Player.log")
        elif user.game_biz == GameBiz.GLOBAL.value:
            return Path(MHY_LOG_ROOT_PATH, GameLogPath.GLOBAL.value, "Player.log")


class GameClient:
    def __init__(self, user: Account) -> None:
        self.user = user

    def get_game_path(self):
        log_path = GameLogPath.get_by_user(self.user)
        if not log_path.exists():
            logger.error(_lang.game_log_not_found)
            return None
        try:
            log_text = log_path.read_text(encoding="utf8")
        except UnicodeDecodeError as err:
            logger.debug(f"日志文件编码不是utf8, 尝试默认编码 {err}")
            log_text = log_path.read_text(encoding=None)

        res = re.search("([A-Z]:/.+StarRail_Data)", log_text)
        game_path = res.group() if res else None
        return game_path

    def get_webcache_path(self):
        game_path = self.get_game_path()
        if not game_path:
            logger.error(_lang.game_path_not_found)
            return None
        cache_root_path = os.path.join(game_path, "webCaches")
        data_2_files = glob.glob(os.path.join(cache_root_path, "*", "Cache/Cache_Data/data_2"))
        if not data_2_files:
            logger.error(_lang.game_webcache_file_not_found)
            return None
        data_2_files = sorted(data_2_files, key=lambda file: os.path.getmtime(file), reverse=True)

        return data_2_files[0]
