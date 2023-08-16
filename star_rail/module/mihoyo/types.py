import enum

from star_rail.exceptions import ParamValueError


class GameBiz(str, enum.Enum):
    GLOBAL = "hkrpg_global"
    CN = "hkrpg_cn"

    @staticmethod
    def get_by_uid(uid):
        if "6" <= uid[0] <= "9":
            return GameBiz.GLOBAL
        elif "1" <= uid[0] <= "5":
            return GameBiz.CN
        else:
            # 不会触发
            raise ParamValueError(f"Invalid UID value: {uid}")


class Region(str, enum.Enum):
    """Game server region"""

    CN_GF = "prod_gf_cn"
    CN_QD = "prod_qd_cn"
    ASIA = "prod_official_asia"
    USA = "prod_official_usa"
    EUR = "prod_official_euro"
    CHT = "prod_official_cht"

    @staticmethod
    def get_by_uid(uid: str):
        _region_dict = {
            "1": Region.CN_GF,
            "2": Region.CN_GF,
            "5": Region.CN_QD,
            "6": Region.USA,
            "7": Region.EUR,
            "8": Region.ASIA,
            "9": Region.CHT,
        }
        return _region_dict.get(uid[0], Region.CN_GF)


class GameType(int, enum.Enum):
    GENSHIN = 2

    STAR_RAIL = 6
