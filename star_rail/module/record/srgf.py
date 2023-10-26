"""
SRGF 星穹铁道抽卡记录标准
https://uigf.org/zh/standards/SRGF.html
"""

import time

from pydantic import BaseModel, Field, field_validator

from star_rail import __version__ as app_version
from star_rail import constants
from star_rail.module.types import Region
from star_rail.utils.time import get_format_time, local_time_to_timezone
from star_rail.utils.version import get_version

from .model import BaseGachaItem, GachaItem, GachaRecordInfo

__all__ = ["convert_to_gacha_record", "convert_to_srgf"]


SRGF_VERSION = (1, 0)


def get_srgf_version(srgf_version):
    return "v" + get_version(srgf_version)


class SrgfInfo(BaseModel):
    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int = 0
    export_time: str = "-"
    export_app: str = "-"
    export_app_version: str = "-"
    srgf_version: str = Field(default=get_srgf_version(SRGF_VERSION))

    from star_rail.module.account.account import verify_uid_format

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    @classmethod
    def create(cls, uid: str, lang: str, region_time_zone: int):
        local_std_time = time.localtime(time.time())
        origin_time = local_time_to_timezone(local_std_time, region_time_zone)

        export_app_version = app_version
        return SrgfInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(time.mktime(origin_time)),
            export_time=get_format_time(time.mktime(origin_time)),
            export_app=constants.APP_NAME,
            export_app_version=export_app_version,
        )


class SrgfGachaItem(BaseGachaItem):
    count: str = "1"
    name: str = "-"
    rank_type: str = "-"
    item_type: str = "-"


class SrgfData(BaseModel):
    info: SrgfInfo
    list: list[SrgfGachaItem]


def convert_to_gacha_record(data: SrgfData) -> tuple[GachaRecordInfo, list[GachaItem]]:
    record_info = GachaRecordInfo(
        uid=data.info.uid,
        lang=data.info.lang,
        region=Region.get_by_uid(data.info.uid).value,
        region_time_zone=data.info.region_time_zone,
    )
    item_list = [
        GachaItem(uid=record_info.uid, lang=record_info.lang, **item.model_dump())
        for item in data.list
    ]

    return record_info, sorted(item_list, key=lambda item: item.id)


def convert_to_srgf(info: GachaRecordInfo, data: list[GachaItem]):
    srgf_info = SrgfInfo.create(info.uid, lang=info.lang, region_time_zone=info.region_time_zone)
    srgf_list = [SrgfGachaItem(**item.model_dump()) for item in data]
    return SrgfData(info=srgf_info, list=srgf_list)
