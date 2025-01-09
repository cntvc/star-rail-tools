from __future__ import annotations

import os
import typing

from loguru import logger

from star_rail import constants
from star_rail.database import DB_VERSION, DbClient
from star_rail.logger import init_logger

from .account import Account, AccountClient
from .metadata import HakushMetadata
from .record import GACHA_TYPE_DICT, ExportHelper, GachaRecordClient, ImportHelper
from .updater import Updater

if typing.TYPE_CHECKING:
    from .metadata import BaseMetadata


__all__ = ["HSRClient", "Account", "GACHA_TYPE_DICT"]


_default_metadata = HakushMetadata()


class HSRClient(GachaRecordClient, ExportHelper, ImportHelper, AccountClient):
    user: Account
    metadata: BaseMetadata

    def __init__(self, user: Account | None = None, _metadata: BaseMetadata = _default_metadata):
        init_logger()
        super().__init__(user, _metadata)
        self.updater = Updater()
        self.metadata_is_latest = False

    async def init(self):
        self._init_app_path()
        await self._init_db()
        await self.init_default_account()

    async def _init_db(self):
        if not os.path.exists(DbClient.DB_PATH):
            logger.debug("Create database")
            async with DbClient() as db:
                await db.create_all_table()
                await db.set_user_version(DB_VERSION)
            return

        async with DbClient() as db:
            local_db_version = await db.get_user_version()
            logger.debug(
                "Local db version: {}, current db version: {}", local_db_version, DB_VERSION
            )

            if local_db_version < DB_VERSION:
                db_manager = db.upgrade_manager()
                await db_manager.backup_database()
                await db_manager.upgrade_database()

    def _init_app_path(self):
        path_variables = [path for name, path in vars(constants).items() if name.endswith("_PATH")]
        for path in path_variables:
            os.makedirs(path, exist_ok=True)

    async def check_app_update(self):
        return await self.updater.check_update()

    async def get_changelog(self, page_size: int = 5):
        return await self.updater.get_changelog(page_size)

    async def check_and_update_metadata(self):
        if await self.metadata.check_update():
            await self.metadata.update()
        self.metadata_is_latest = True
