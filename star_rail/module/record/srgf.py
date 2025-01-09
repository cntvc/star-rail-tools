"""
SRGF 星穹铁道抽卡记录标准

https://uigf.org/zh/standards/srgf.html
"""

from pydantic import BaseModel, field_validator

from star_rail import __version__ as app_version
from star_rail import constants
from star_rail.utils import Date

from .entity import GachaRecordBatchEntity
from .model import BaseGachaRecordItem, GachaRecordItem

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

    from star_rail.module.account import verify_uid_format

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    @field_validator("srgf_version", mode="before")
    @classmethod
    def _verify_version(cls, v: str):
        if not isinstance(v, str):
            raise ValueError(f"无效的 SRGF version 类型: {type(v)}")
        if v != SRGF_VERSION:
            raise ValueError(f"未受支持的 SRGF version : {v}")
        return v

    @classmethod
    def build(cls, uid: str, lang: str, region_time_zone: int):
        datetime = Date.local_time_to_timezone(region_time_zone)
        export_app_version = app_version
        print(datetime, export_app_version, uid, lang, region_time_zone, SRGF_VERSION)
        return cls(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(datetime.timestamp()),
            export_time=datetime.strftime(Date.Format.YYYY_MM_DD_HHMMSS),
            export_app=constants.APP_NAME,
            export_app_version=export_app_version,
            srgf_version=SRGF_VERSION,
        )


class SRGFItem(BaseGachaRecordItem):
    count: str = "1"
    name: str = "-"
    rank_type: str = "-"
    item_type: str = "-"


class SRGFData(BaseModel):
    info: SRGFInfo
    list: list[SRGFItem]


def convert_srgf_to_record(
    srgf_data: SRGFData,
) -> tuple[list[GachaRecordItem], SRGFInfo]:
    item_list = [
        GachaRecordItem(uid=srgf_data.info.uid, lang=srgf_data.info.lang, **item.model_dump())
        for item in srgf_data.list
    ]
    item_list.sort(key=lambda x: x.id)
    return item_list, srgf_data.info


def convert_record_to_srgf(gacha_record_item: list[GachaRecordItem], batch: GachaRecordBatchEntity):
    srgf_info = SRGFInfo.build(batch.uid, lang=batch.lang, region_time_zone=batch.region_time_zone)
    srgf_list = [SRGFItem(**item.model_dump()) for item in gacha_record_item]
    return SRGFData(info=srgf_info, list=srgf_list)
