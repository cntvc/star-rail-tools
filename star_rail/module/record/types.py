import enum
import typing

from star_rail.i18n import i18n


class GachaRecordType(str, enum.Enum):
    REGULAR_WARP = "1"
    STARTER_WARP = "2"
    CHARACTER_EVENT_WARP = "11"
    LIGHT_CONE_EVENT_WARP = "12"


GACHA_TYPE_IDS: list[str] = [member.value for member in GachaRecordType]
"""抽卡类型列表"""

GACHA_TYPE_DICT: typing.OrderedDict[str, str] = typing.OrderedDict(
    {
        GachaRecordType.REGULAR_WARP.value: i18n.regular_warp,
        GachaRecordType.STARTER_WARP.value: i18n.starter_warp,
        GachaRecordType.CHARACTER_EVENT_WARP.value: i18n.character_event_warp,
        GachaRecordType.LIGHT_CONE_EVENT_WARP.value: i18n.light_cone_event_warp,
    }
)
"""[抽卡类型ID:抽卡类型名]"""
