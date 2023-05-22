import enum
import os
import re
from pathlib import Path

from star_rail.i18n import i18n
from star_rail.module.account import Account, GameBizType
from star_rail.utils.log import logger

_lang = i18n.game_client

MHY_LOG_ROOT_PATH = os.path.join(os.getenv("USERPROFILE"), "AppData", "LocalLow")


class GameLogPath(str, enum.Enum):
    CN = "miHoYo/崩坏：星穹铁道/"
    GLOBAL = "Cognosphere/Star Rail/"

    @staticmethod
    def get_by_user(user: Account):
        if user.game_biz == GameBizType.CN.value:
            return Path(MHY_LOG_ROOT_PATH, GameLogPath.CN.value, "Player.log")
        elif user.game_biz == GameBizType.GLOBAL.value:
            return Path(MHY_LOG_ROOT_PATH, GameLogPath.GLOBAL.value, "Player.log")


class GameClient:
    _WEB_CACHE_PATH = "webCaches/Cache/Cache_Data/data_2"
    _GAME_DATA_DIR_NAME = "StarRail_Data"

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

        res = re.search("([A-Z]:/.+{})".format(GameClient._GAME_DATA_DIR_NAME), log_text)
        game_path = res.group() if res else None
        return game_path

    def get_webcache_path(self):
        game_path = self.get_game_path()
        if not game_path:
            logger.error(_lang.game_path_not_found)
            return None
        data_2_path = os.path.join(game_path, GameClient._WEB_CACHE_PATH)
        if not os.path.isfile(data_2_path):
            logger.error(_lang.game_webcache_file_not_found)
            return None
        return data_2_path
