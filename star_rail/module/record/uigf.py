import re

from pydantic import BaseModel, field_validator

from star_rail import __version__ as app_version
from star_rail import constants
from star_rail.utils import Date

from .entity import GachaRecordBatchEntity
from .model import BaseGachaRecordItem, GachaRecordItem

UIGF_VERSION_V4_0 = "v4.0"

SUPPORT_UIGF_VERSIONS = [UIGF_VERSION_V4_0]

_uigf_version_re = re.compile(r"^v\d+\.\d+$")


class UIGFInfo(BaseModel):
    export_time: str
    export_timestamp: int
    """导出档案的时间戳，秒级"""
    export_app: str
    export_app_version: str
    version: str
    """导出档案的 UIGF 版本号，格式为 'v{major}.{minor}' """

    @field_validator("version", mode="before")
    @classmethod
    def _verify_version(cls, version: str):
        if version is None:
            raise ValueError("UIGF 'version' 值不能为 None")
        if not _uigf_version_re.fullmatch(version):
            raise ValueError("无效的 UIGF 'version' 格式")
        if version not in SUPPORT_UIGF_VERSIONS:
            raise ValueError(f"尚未受支持的 UIGF 版本：{version}")
        return version


class UIGFItem(BaseGachaRecordItem):
    count: str = "1"
    name: str = "-"
    item_type: str = "-"
    rank_type: str = "-"


class UIGFUserRecord(BaseModel):
    uid: str
    timezone: int
    lang: str = ""
    list: list[UIGFItem]


class UIGFData(BaseModel):
    info: UIGFInfo
    hkrpg: list[UIGFUserRecord] = []


def convert_record_to_uigf(
    gacha_record_item: list[GachaRecordItem], batch: GachaRecordBatchEntity
) -> UIGFData:
    datetime = Date.local_time_to_timezone(batch.region_time_zone)
    uigf_info = UIGFInfo(
        export_time=datetime.strftime(Date.Format.YYYY_MM_DD_HHMMSS),
        export_timestamp=int(datetime.timestamp()),
        export_app=constants.APP_NAME,
        export_app_version=app_version,
        version=UIGF_VERSION_V4_0,
    )
    uigf_record_item_list = [UIGFItem(**item.model_dump()) for item in gacha_record_item]
    uigf_record = UIGFUserRecord(
        uid=batch.uid, timezone=batch.region_time_zone, lang=batch.lang, list=uigf_record_item_list
    )
    return UIGFData(info=uigf_info, hkrpg=[uigf_record])
