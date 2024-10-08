"""
SRGF 星穹铁道抽卡记录标准

https://uigf.org/zh/standards/SRGF.html
"""

from pydantic import BaseModel, field_validator

from star_rail import __version__ as app_version
from star_rail import constants
from star_rail.utils.date import Date

from .mapper import GachaRecordBatchMapper
from .model import BaseGachaRecordItem, GachaRecordItem

__all__ = ["convert_to_gacha_record_data", "convert_to_srgf"]


SRGF_VERSION = "v1.0"


class SRGFInfo(BaseModel):
    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int = 0
    export_time: str = "-"
    export_app: str = "-"
    export_app_version: str = "-"
    srgf_version: str

    from star_rail.module.account.account import verify_uid_format

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    @classmethod
    def create(cls, uid: str, lang: str, region_time_zone: int):
        datetime = Date.local_to_timezone(region_time_zone)
        export_app_version = app_version
        return SRGFInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(datetime.timestamp()),
            export_time=Date.format_time(datetime),
            export_app=constants.APP_NAME,
            export_app_version=export_app_version,
            srgf_version=SRGF_VERSION,
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
) -> tuple[list[GachaRecordItem], SRGFInfo]:
    """

    Returns:
        tuple[list[GachaRecordItem], SRGFInfo]: 抽卡记录列表, 抽卡记录信息
    """
    item_list = [
        GachaRecordItem(uid=srgf_data.info.uid, lang=srgf_data.info.lang, **item.model_dump())
        for item in srgf_data.list
    ]
    item_list.sort(key=lambda x: x.id)
    return item_list, srgf_data.info


def convert_to_srgf(gacha_record_item: list[GachaRecordItem], batch: GachaRecordBatchMapper):
    srgf_info = SRGFInfo.create(batch.uid, lang=batch.lang, region_time_zone=batch.region_time_zone)
    srgf_list = [SRGFRecordItem(**item.model_dump()) for item in gacha_record_item]
    return SRGFData(info=srgf_info, list=srgf_list)
