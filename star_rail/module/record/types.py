import enum

__all__ = ["GachaRecordType", "GACHA_TYPE_IDS", "GACHA_TYPE_DICT"]


class GachaRecordType(enum.StrEnum):
    REGULAR_WARP = "1"
    STARTER_WARP = "2"
    CHARACTER_EVENT_WARP = "11"
    CHARACTER_COLLABORATION_WARP = "21"
    LIGHT_CONE_EVENT_WARP = "12"
    LIGTH_CONE_COLLABORATION_WARP = "22"

    @staticmethod
    def get_by_value(val: str):
        for member in GachaRecordType.__members__.values():
            if member.value == val:
                return member
        raise AssertionError(f"Param value error, got [{val}].")


GACHA_TYPE_IDS: list[str] = [member.value for member in GachaRecordType]
"""抽卡类型列表"""

GACHA_TYPE_DICT = {
    GachaRecordType.REGULAR_WARP.value: "常驻跃迁",
    GachaRecordType.CHARACTER_EVENT_WARP.value: "角色活动跃迁",
    GachaRecordType.LIGHT_CONE_EVENT_WARP.value: "光锥活动跃迁",
    GachaRecordType.CHARACTER_COLLABORATION_WARP.value: "角色联动跃迁",
    GachaRecordType.LIGTH_CONE_COLLABORATION_WARP.value: "光锥联动跃迁",
    GachaRecordType.STARTER_WARP.value: "新手跃迁",
}

"""[抽卡类型ID:抽卡类型名]"""
