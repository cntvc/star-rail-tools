import os

from star_rail.database import DATABASE_VERSION, DBManager
from star_rail.utils.logger import logger

from .account import *
from .month import *
from .record import *
from .updater import Updater

__all__ = ["HSRClient", "Updater"]


class HSRClient(AccountClient, GachaRecordClient, MonthInfoClient):
    async def start(self):
        db_manager = DBManager()
        if not os.path.exists(db_manager.db_path):
            logger.debug("init database.")
            await db_manager.create_all()
            await db_manager.set_user_version(DATABASE_VERSION)
        cur_db_version = await db_manager.user_version()
        logger.debug("Current db version: {}.", cur_db_version)
        if cur_db_version < DATABASE_VERSION:
            await db_manager.upgrade_database()

        await self.init_default_account()
