import enum
import typing

from star_rail.i18n import i18n


class GachaType(str, enum.Enum):
    REGULAR_WARP = "1"
    STARTER_WARP = "2"
    CHARACTER_EVENT_WARP = "11"
    LIGHT_CONE_EVENT_WARP = "12"


GACHA_TYPE_IDS: typing.List[str] = [member.value for member in GachaType]
"""抽卡类型列表"""

GACHA_TYPE_DICT: typing.Dict[str, str] = {
    GachaType.REGULAR_WARP.value: i18n.regular_warp,
    GachaType.STARTER_WARP.value: i18n.starter_warp,
    GachaType.CHARACTER_EVENT_WARP.value: i18n.character_event_warp,
    GachaType.LIGHT_CONE_EVENT_WARP.value: i18n.light_cone_event_warp,
}
"""[抽卡类型:语言字典]"""
