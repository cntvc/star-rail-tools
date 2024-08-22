import os

from star_rail.database import DATABASE_VERSION, DBManager
from star_rail.utils.logger import logger

from .account import *
from .info import get_sys_info
from .metadata import HakushMetadata
from .metadata.base import BaseMetadata
from .month import *
from .record import *
from .updater import Updater

__all__ = ["HSRClient", "get_sys_info"]


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

    async def check_update(self):
        return await Updater().check_update()
