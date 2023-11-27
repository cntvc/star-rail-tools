"""
SRGF 星穹铁道抽卡记录标准

https://uigf.org/zh/standards/SRGF.html
"""

import typing

from pydantic import BaseModel, Field, field_validator

from star_rail import __version__ as app_version
from star_rail import constants
from star_rail.utils.time import TimeUtils
from star_rail.utils.version import get_version

from .mapper import GachaRecordBatchMapper
from .model import BaseGachaRecordItem, GachaRecordItem

__all__ = ["convert_to_gacha_record_data", "convert_to_srgf"]


SRGF_VERSION = (1, 0)


def get_srgf_version(srgf_version):
    return "v" + get_version(srgf_version)


class SRGFInfo(BaseModel):
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
        local_std_time = TimeUtils.get_local_time()
        origin_time = TimeUtils.local_time_to_timezone(local_std_time, region_time_zone)

        export_app_version = app_version
        return SRGFInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=TimeUtils.convert_to_timestamp(origin_time),
            export_time=TimeUtils.get_format_time(TimeUtils.convert_to_time(origin_time)),
            export_app=constants.APP_NAME,
            export_app_version=export_app_version,
        )


class SRGFRecordItem(BaseGachaRecordItem):
    count: str = "1"
    name: str = "-"
    rank_type: str = "-"
    item_type: str = "-"


class SRGFData(BaseModel):
    info: SRGFInfo
    list: list[SRGFRecordItem]


def convert_to_gacha_record_data(
    srgf_data: SRGFData,
) -> tuple[list[GachaRecordItem], dict[str, typing.Any]]:
    """

    Returns:
        tuple[list[GachaRecordItem], dict[str, typing.Any]]: 抽卡记录列表, 抽卡记录信息
            dict:(uid, lang, region_time_zone, source)
    """
    info = {
        "uid": srgf_data.info.uid,
        "lang": srgf_data.info.lang,
        "region_time_zone": srgf_data.info.region_time_zone,
        "source": srgf_data.info.export_app,
    }
    item_list = [
        GachaRecordItem(uid=srgf_data.info.uid, lang=srgf_data.info.lang, **item.model_dump())
        for item in srgf_data.list
    ]
    item_list.sort(key=lambda x: x.id)
    return item_list, info


def convert_to_srgf(gacha_record_item: list[GachaRecordItem], batch: GachaRecordBatchMapper):
    srgf_info = SRGFInfo.create(batch.uid, lang=batch.lang, region_time_zone=batch.region_time_zone)
    srgf_list = [SRGFRecordItem(**item.model_dump()) for item in gacha_record_item]
    return SRGFData(info=srgf_info, list=srgf_list)
