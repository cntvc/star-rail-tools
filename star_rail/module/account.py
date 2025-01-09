import os.path
import re
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, field_serializer, field_validator

from star_rail import constants, exceptions
from star_rail.config import config
from star_rail.database import DbClient, DbField, DbModel

from .base import BaseClient
from .types import GameBiz, Region


def verify_uid_format(v):
    if Account.verify_uid(v):
        return v
    raise ValueError(f"UID 格式错误: {v}")


class Account(BaseModel):
    uid: str

    # 以下成员根据 uid 初始化
    region: Region = None
    game_biz: GameBiz = None

    analyze_result_path: Path = ""
    srgf_path: Path = ""
    uigf_path: Path = ""
    gacha_record_xlsx_path: Path = ""

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    def __init__(self, uid: str, **data):
        super().__init__(uid=uid, **data)
        self.gacha_record_xlsx_path = Path(
            constants.USERDATA_PATH, self.uid, f"GachaRecord_{self.uid}.xlsx"
        )
        self.srgf_path = Path(
            constants.USERDATA_PATH, self.uid, f"GachaRecord_SRGF_{self.uid}.json"
        )
        self.uigf_path = Path(
            constants.USERDATA_PATH, self.uid, f"GachaRecord_UIGF_{self.uid}.json"
        )
        self.analyze_result_path = Path(constants.TEMP_PATH, f"GachaRecordAnalyze_{self.uid}.json")
        self.game_biz = GameBiz.get_by_uid(self.uid)
        self.region = Region.get_by_uid(self.uid)

    @field_serializer("region")
    def serialize_region(self, region: Region):
        return region.value

    @field_serializer("game_biz")
    def serialize_game_biz(self, game_biz: GameBiz):
        return game_biz.value

    @staticmethod
    async def exists(uid: str) -> bool:
        return bool(await AccountDbClient.query_by_uid(uid))

    async def save_profile(self) -> bool:
        logger.debug("Save profile. Account: {}", self.uid)

        account_entity = AccountEntity(
            uid=self.uid,
            region=self.region,
            game_biz=self.game_biz,
        )
        return bool(await AccountDbClient.add(account_entity))

    @staticmethod
    def verify_uid(v):
        return isinstance(v, str) and _UID_RE.fullmatch(v) is not None


class AccountEntity(DbModel):
    __table_name__ = "user"

    uid: str = DbField(primary_key=True)

    region: str

    game_biz: str


class AccountDbClient(BaseClient):
    @staticmethod
    async def query_by_uid(uid: str) -> AccountEntity | None:
        sql = """select * from user where uid = ?;"""
        async with DbClient() as db:
            cursor = await db.execute(sql, uid)
            row = await cursor.fetchone()
            return db.convert(row, AccountEntity)

    @staticmethod
    async def query_all_uid() -> list[str]:
        sql = """select uid from user order by uid;"""
        async with DbClient() as db:
            cursor = await db.execute(sql)
            return [r[0] for r in await cursor.fetchall()]

    @staticmethod
    async def add(account_entity: AccountEntity) -> int:
        async with DbClient() as db:
            return await db.insert(account_entity, mode="replace")

    @staticmethod
    async def delete(uid: str) -> None:
        async with DbClient() as db:
            await db.start_transaction()
            await db.execute("delete from user where uid = ?;", uid)
            await db.execute("delete from gacha_record_batch where uid = ?;", uid)
            await db.execute("delete from gacha_record_item where uid = ?;", uid)
            await db.commit_transaction()


_UID_RE = re.compile("^[1-9][0-9]{8}$")


class AccountClient(BaseClient):
    async def init_default_account(self):
        logger.debug("Initializing default account")
        if not config.DEFAULT_UID:
            return

        if await Account.exists(config.DEFAULT_UID):
            self.user = Account(config.DEFAULT_UID)
            return

        # 本地配置文件记录了但数据库无数据，重置配置文件 DEFAULT_UID
        config.DEFAULT_UID = ""
        config.save()

    async def login(self, uid: str):
        if not await Account.exists(uid):
            raise exceptions.GachaRecordError("未找到账号 {} 数据", uid)
        self.user = Account(uid)
        config.DEFAULT_UID = uid
        config.save()
        logger.debug("Login account: {}", uid)

    async def logout(self):
        logger.debug("Logout account: {}", self.user.uid)
        if self.user.uid == config.DEFAULT_UID:
            config.DEFAULT_UID = ""
            config.save()
        self.user = None

    @staticmethod
    async def create_account(uid: str):
        if await Account.exists(uid):
            logger.debug("Account already exists: {}", uid)
            return Account(uid)
        user = Account(uid)
        await user.save_profile()
        logger.debug("Created account successfully: {}", uid)
        return user

    @staticmethod
    async def delete_account(uid: str):
        logger.debug("Delete account: {}", uid)
        if not await Account.exists(uid):
            raise exceptions.GachaRecordError("未找到账号 {} 数据", uid)
        user = Account(uid)
        await AccountDbClient.delete(uid)

        paths_to_delete = [
            user.srgf_path.as_posix(),
            user.uigf_path.as_posix(),
            user.analyze_result_path.as_posix(),
            user.gacha_record_xlsx_path.as_posix(),
        ]
        for path in paths_to_delete:
            if os.path.exists(path):
                os.remove(path)
                logger.debug("Delete file: {}", path)

    async def get_uid_list(self) -> list[str]:
        return await AccountDbClient.query_all_uid()
