import enum

__all__ = ["GameBiz", "Region", "GameType"]


class GameBiz(enum.StrEnum):
    GLOBAL = "hkrpg_global"
    CN = "hkrpg_cn"

    @staticmethod
    def get_by_uid(uid):
        if "6" <= uid[0] <= "9":
            return GameBiz.GLOBAL
        elif "1" <= uid[0] <= "5":
            return GameBiz.CN
        else:
            assert False, f"Param value error, got [{uid}]."

    @staticmethod
    def get_by_str(val: str):
        for member in GameBiz.__members__.values():
            if member.value == val:
                return member
        assert False, f"Param value error, got [{val}]."


class Region(enum.StrEnum):
    CN_GF = "prod_gf_cn"
    CN_QD = "prod_qd_cn"
    ASIA = "prod_official_asia"
    USA = "prod_official_usa"
    EURO = "prod_official_euro"
    CHT = "prod_official_cht"

    @staticmethod
    def get_by_uid(uid: str):
        _region_dict = {
            "1": Region.CN_GF,
            "2": Region.CN_GF,
            "5": Region.CN_QD,
            "6": Region.USA,
            "7": Region.EURO,
            "8": Region.ASIA,
            "9": Region.CHT,
        }
        return _region_dict.get(uid[0], Region.CN_GF)

    @staticmethod
    def get_by_str(val: str):
        for member in Region.__members__.values():
            if member.value == val:
                return member
        assert False, f"Param value error, got [{val}]."


class GameType(enum.IntEnum):
    GENSHIN = 2

    STAR_RAIL = 6
