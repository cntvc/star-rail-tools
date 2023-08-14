import time
from typing import List

from pydantic import BaseModel, validator

from star_rail import __version__ as version
from star_rail import constants
from star_rail.module.mihoyo.account import verify_uid_format
from star_rail.utils.time import convert_time_to_timezone, get_format_time
from star_rail.utils.version import get_version

from .gacha_log import BaseGachaItem, GachaInfo, GachaType

SRGF_VERSION = (1, 0)


def get_srgf_version(srgf_version):
    return "v" + get_version(srgf_version)


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

    _verify_uid_format = validator("uid", always=True, allow_reuse=True)(verify_uid_format)

    @staticmethod
    def gen(uid: str, lang: str, region_time_zone: int):
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
    list: List[SrgfGachaItem]


def convert_to_srgf(gacha_data: dict):
    info = gacha_data["info"]
    srgf_info = SrgfInfo.gen(info["uid"], info["lang"], info["region_time_zone"])
    gacha_item_list = []
    for gacha_type in GachaType.list():
        gacha_item_list.extend(gacha_data["gacha_log"][gacha_type])
    return SrgfData(info=srgf_info, list=gacha_item_list)


def convert_to_app(srgf_data: dict):
    """SRGF 转 app 格式"""
    info = srgf_data["info"]
    for item in srgf_data["list"]:
        item["uid"] = info["uid"]
        item["lang"] = info["lang"]

    gacha_log = {}
    for gacha_type in GachaType.list():
        gacha_log[gacha_type] = sorted(
            [item for item in srgf_data["list"] if item["gacha_type"] == gacha_type],
            key=lambda x: x["id"],
        )
    gacha_data = {}
    gacha_data["info"] = GachaInfo.gen(
        info["uid"], info["lang"], info["region_time_zone"]
    ).model_dump()
    gacha_data["gacha_type"] = GachaType.dump_dict()
    gacha_data["gacha_log"] = gacha_log
    return gacha_data


def is_srgf_data(data):
    return (
        "info" in data
        and "srgf_version" in data["info"]
        and "uid" in data["info"]
        and "list" in data
    )
