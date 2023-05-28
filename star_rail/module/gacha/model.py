import enum
import time

from pydantic import BaseModel

from star_rail import __version__ as version
from star_rail import constants
from star_rail.i18n import i18n
from star_rail.utils import functional


class GachaType(str, enum.Enum):
    REGULAR_WARP = "1"
    STARTER_WARP = "2"
    CHARACTER_EVENT_WARP = "11"
    LIGHT_CONE_EVENT_WARP = "12"

    @staticmethod
    def dict():
        return {
            GachaType.REGULAR_WARP.value: i18n.regular_warp,
            GachaType.STARTER_WARP.value: i18n.starter_warp,
            GachaType.CHARACTER_EVENT_WARP.value: i18n.character_event_warp,
            GachaType.LIGHT_CONE_EVENT_WARP.value: i18n.light_cone_event_warp,
        }

    @staticmethod
    def list():
        return [member.value for member in GachaType]


SRGF_VERSION = "1.0.0"


class GachaInfo(BaseModel):
    uid: str
    lang: str
    region_time_zone: int
    export_timestamp: int
    export_time: str
    export_app: str
    export_app_version: str

    def __init__(self, uid: str, lang: str, region_time_zone: int = None):
        local_std_time = time.localtime(time.time())
        if region_time_zone is None:
            # 用于兼容 1.0.1 及以下版本数据
            region_time_zone = functional.get_timezone(local_std_time)
        origin_time = functional.convert_time_to_timezone(local_std_time, region_time_zone)

        export_app = constants.APP_NAME
        export_app_version = version
        super().__init__(
            uid=uid,
            lang=lang,
            region_time_zone=region_time_zone,
            export_timestamp=int(time.mktime(origin_time)),
            export_time=functional.get_format_time(time.mktime(origin_time)),
            export_app=export_app,
            export_app_version=export_app_version,
        )


class SrgfInfo(GachaInfo):
    srgf_version: str = SRGF_VERSION
