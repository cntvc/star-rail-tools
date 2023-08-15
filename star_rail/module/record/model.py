import time
import typing

from pydantic import BaseModel, field_validator

from star_rail import __version__ as version
from star_rail import constants


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


class SrgfInfo(BaseModel):
    """SRGF v1.0 info"""

    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int = 0
    export_time: str = "-"
    export_app: str = "-"
    export_app_version: str = "-"
    srgf_version: str

    from star_rail.module.mihoyo.account import verify_uid_format

    _verify_uid_format = field_validator("uid", mode="before")(verify_uid_format)

    @classmethod
    def gen(cls, uid: str, lang: str, region_time_zone: int):
        from star_rail.module.record.srgf import SRGF_VERSION, get_srgf_version
        from star_rail.utils.time import convert_time_to_timezone, get_format_time

        local_std_time = time.localtime(time.time())
        origin_time = convert_time_to_timezone(local_std_time, region_time_zone)

        export_app = constants.APP_NAME
        export_app_version = version
        return SrgfInfo(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(time.mktime(origin_time)),
            export_time=get_format_time(time.mktime(origin_time)),
            export_app=export_app,
            export_app_version=export_app_version,
            srgf_version=get_srgf_version(SRGF_VERSION),
        )


class SrgfGachaItem(BaseGachaItem):
    count: str = "1"
    name: str = "-"
    rank_type: str = "-"
    item_type: str = "-"


class SrgfData(BaseModel):
    info: SrgfInfo
    list: typing.List[SrgfGachaItem]


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
