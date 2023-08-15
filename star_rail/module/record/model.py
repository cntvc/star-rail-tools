import time
import typing

from pydantic import BaseModel, Field, field_validator

from star_rail import __version__ as version
from star_rail import constants
from star_rail.utils.version import get_version


class BaseGachaItem(BaseModel):
    gacha_id: str
    gacha_type: str
    item_id: str
    time: str
    id: str

    def __eq__(self, __value: "BaseGachaItem") -> bool:
        return self.id == __value.id

    def __ne__(self, __value: "BaseGachaItem") -> bool:
        return self.id != __value.id

    def __gt__(self, __value: "BaseGachaItem") -> bool:
        return self.id > __value.id

    def __lt__(self, __value: "BaseGachaItem") -> bool:
        return self.id < __value.id


class GachaItem(BaseGachaItem):
    count: str
    name: str
    rank_type: str
    uid: str
    lang: str
    item_type: str


class GachaData(BaseModel):
    page: int
    size: int
    list: typing.List[GachaItem]
    region: str
    region_time_zone: int


class GachaRecordInfo(BaseModel):
    uid: str

    lang: str

    region: str

    region_time_zone: int


########################################################################
# SRGF
########################################################################

SRGF_VERSION = (1, 0)


def get_srgf_version(srgf_version):
    return "v" + get_version(srgf_version)


class SRGFInfo(BaseModel):
    """SRGF v1.0 info"""

    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int = 0
    export_time: str = "-"
    export_app: str = "-"
    export_app_version: str = "-"
    srgf_version: str = Field(default=get_srgf_version(SRGF_VERSION))

    from star_rail.module.mihoyo.account import verify_uid_format

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    @classmethod
    def gen(cls, uid: str, lang: str, region_time_zone: int):
        from star_rail.utils.time import convert_time_to_timezone, get_format_time

        local_std_time = time.localtime(time.time())
        origin_time = convert_time_to_timezone(local_std_time, region_time_zone)

        export_app_version = version
        return SRGFInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(time.mktime(origin_time)),
            export_time=get_format_time(time.mktime(origin_time)),
            export_app=constants.APP_NAME,
            export_app_version=export_app_version,
        )


class SRGFRecordItem(BaseGachaItem):
    count: str = "1"
    name: str = "-"
    rank_type: str = "-"
    item_type: str = "-"


class SRGFData(BaseModel):
    info: SRGFInfo
    list: typing.List[SRGFRecordItem]


########################################################################
# Analyze
########################################################################


class AnalyzeDataRecordItem(GachaItem):
    # 添加索引表示抽数
    number: str


class AnalyzeData(BaseModel):
    """分卡池的分析结果类"""

    gacha_type: str = ""
    pity_count: int = 0
    total_count: int = 0
    list: typing.List[AnalyzeDataRecordItem] = []


class AnalyzeResult(BaseModel):
    uid: str = ""
    lang: str = ""
    update_time: str = ""
    data: typing.List[AnalyzeData] = []
