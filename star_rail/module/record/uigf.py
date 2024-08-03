import re

from pydantic import BaseModel, field_validator

from star_rail import __version__ as app_version
from star_rail import constants

from ...utils.date import Date
from .mapper import GachaRecordBatchMapper
from .model import GachaRecordItem

UIGF_VERSION_V4 = "v4.0"

SUPPORT_UIGF_VERSIONS = [UIGF_VERSION_V4]

_uigf_version_re = re.compile(r"^v\d+\.\d+$")


class UIGFInfo(BaseModel):
    export_time: str
    export_timestamp: int
    """导出档案的时间戳，秒级"""
    export_app: str
    export_app_version: str
    version: str
    """导出档案的 UIGF 版本号，格式为 'v{major}.{minor}' """

    @field_validator("version")
    @classmethod
    def _valid_version(cls, version: str):
        if version is None:
            raise ValueError("Empty version")
        if not _uigf_version_re.fullmatch(version):
            raise ValueError("Invalid UIGF version")
        if version not in SUPPORT_UIGF_VERSIONS:
            raise ValueError("Unsupported UIGF version")
        return version


class UIGFRecordItem(BaseModel):
    gacha_id: str
    gacha_type: str
    item_id: str
    count: str = "-"
    time: str
    """抽取物品时对应时区（timezone）下的当地时间"""
    name: str = "-"
    item_type: str = "-"
    rank_type: str = "-"
    id: str


class UIGFRecord(BaseModel):
    uid: str
    timezone: int
    lang: str = "-"
    list: list[UIGFRecordItem]


class UIGFModel(BaseModel):
    info: UIGFInfo
    hkrpg: list[UIGFRecord] = []


def convert_to_uigf(
    gacha_record_item: list[GachaRecordItem], batch: GachaRecordBatchMapper
) -> UIGFModel:
    datetime = Date.local_to_timezone(batch.region_time_zone)
    uigf_info = UIGFInfo(
        export_time=Date.format_time(datetime),
        export_timestamp=int(datetime.timestamp()),
        export_app=constants.APP_NAME,
        export_app_version=app_version,
        version=UIGF_VERSION_V4,
    )
    uigf_record_item_list = [UIGFRecordItem(**item.model_dump()) for item in gacha_record_item]
    uigf_record = UIGFRecord(
        uid=batch.uid, timezone=batch.region_time_zone, lang=batch.lang, list=uigf_record_item_list
    )
    return UIGFModel(info=uigf_info, hkrpg=[uigf_record])
