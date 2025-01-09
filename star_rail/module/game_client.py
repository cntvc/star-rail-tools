from __future__ import annotations

import enum
import glob
import os
import re
import typing
from pathlib import Path

from loguru import logger

from star_rail import exceptions as error

from .base import BaseClient
from .types import GameBiz

if typing.TYPE_CHECKING:
    from star_rail.module.account import Account

_MHY_LOG_ROOT_PATH = os.path.join(os.getenv("USERPROFILE"), "AppData", "LocalLow")


class GameLogPath(str, enum.Enum):
    CN = "miHoYo/崩坏：星穹铁道/"
    GLOBAL = "Cognosphere/Star Rail/"

    @staticmethod
    def get_by_user(user: Account):
        if user.game_biz == GameBiz.CN:
            return Path(_MHY_LOG_ROOT_PATH, GameLogPath.CN.value, "Player.log")
        elif user.game_biz == GameBiz.GLOBAL:
            return Path(_MHY_LOG_ROOT_PATH, GameLogPath.GLOBAL.value, "Player.log")
        else:
            raise AssertionError(f"Param error : [{user.game_biz}]")


class GameClient(BaseClient):
    def get_game_path(self):
        log_path = GameLogPath.get_by_user(self.user)
        if not log_path.exists():
            return None

        try:
            log_text = log_path.read_text(encoding="utf8")
        except UnicodeDecodeError as err:
            logger.debug(f"file encoding format is not utf8, try to use default encoding \n {err}")
            log_text = log_path.read_text(encoding=None)

        res = re.search("([A-Z]:/.+StarRail_Data)", log_text)
        game_path = res.group() if res else None
        return game_path

    def get_web_cache_path(self):
        game_path = self.get_game_path()
        if game_path is None:
            raise error.HsrException("未找到游戏安装路径")
        cache_root_path = os.path.join(game_path, "webCaches")
        data_2_files = glob.glob(os.path.join(cache_root_path, "*", "Cache/Cache_Data/data_2"))
        if not data_2_files:
            raise error.HsrException("未找到网页缓存文件")
        data_2_files = sorted(data_2_files, key=lambda file: os.path.getmtime(file), reverse=True)

        return data_2_files[0]
