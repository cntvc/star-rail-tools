import os
import typing

from star_rail.database import DATABASE_VERSION, DBManager
from star_rail.utils.logger import logger

from .account import *
from .metadata import HakushMetadata
from .metadata.base import BaseMetadata
from .month import *
from .record import *
from .updater import Updater

if typing.TYPE_CHECKING:
    from star_rail.module.account import Account


__all__ = ["HSRClient", "Updater", "HakushMetadata"]


class HSRClient(AccountClient, GachaRecordClient, MonthInfoClient):
    def __init__(self, user: Account = None, metadata: BaseMetadata = None):
        AccountClient.__init__(self, user)
        GachaRecordClient.__init__(self, user, metadata)
        MonthInfoClient.__init__(self, user)

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
