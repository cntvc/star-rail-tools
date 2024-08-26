import os
import shutil
import sys

from star_rail import constants
from star_rail.config import settings
from star_rail.database import DATABASE_VERSION, DBManager
from star_rail.utils.logger import logger

from .account import *
from .metadata import HakushMetadata
from .metadata.base import BaseMetadata
from .month import *
from .record import *
from .updater import Updater

__all__ = ["HSRClient", "HakushMetadata"]


class HSRClient(GachaRecordClient, AccountClient, MonthInfoClient):
    def __init__(self, user: Account = None, _metadata: BaseMetadata = None):
        super().__init__(user, _metadata)

    async def init(self):
        self._init_app_path()

        db_manager = DBManager()
        if not os.path.exists(db_manager.db_path):
            logger.debug("init database.")
            await db_manager.create_all()
            await db_manager.set_user_version(DATABASE_VERSION)
        cur_db_version = await db_manager.user_version()
        logger.debug(
            "Local db version: {}. current db version: {}", cur_db_version, DATABASE_VERSION
        )
        if cur_db_version < DATABASE_VERSION:
            await db_manager.upgrade_database()

        await self.init_default_account()

    def _init_app_path(self):
        from star_rail import constants

        path_variables = [path for name, path in vars(constants).items() if name.endswith("_PATH")]
        for path in path_variables:
            os.makedirs(path, exist_ok=True)

    def migrate_data(self):
        old_root_path = os.path.join(os.path.dirname(sys.argv[0]), "StarRailTools")
        if not os.path.exists(old_root_path):
            return False

        settings.load_config(os.path.join(old_root_path, "AppData", "config", "settings.json"))
        settings.save_config()

        # 单独移动数据库，日志不保留
        shutil.move(os.path.join(old_root_path, "AppData", "data"), constants.APPDATA_PATH)

        for name in os.listdir(old_root_path):
            # Import 目录和 用户导出目录
            if name == "AppData":
                continue
            shutil.move(
                os.path.join(old_root_path, name), os.path.join(constants.USERDATA_PATH, name)
            )

        shutil.rmtree(old_root_path)
        return True

    async def check_update(self):
        return await Updater().check_update()
