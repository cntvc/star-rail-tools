import enum

__all__ = ["GameBiz", "Region"]


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
            raise AssertionError(f"Param type error: [{uid}].")

    @staticmethod
    def get_by_str(val: str):
        for member in GameBiz.__members__.values():
            if member.value == val:
                return member
        raise AssertionError(f"Param type error: [{val}].")


class Region(enum.StrEnum):
    CN_GF = "prod_gf_cn"
    CN_QD = "prod_qd_cn"
    ASIA = "prod_official_asia"
    USA = "prod_official_usa"
    EURO = "prod_official_euro"
    CHT = "prod_official_cht"

    @staticmethod
    def get_by_uid(uid: str):
        region_dict = {
            "1": Region.CN_GF,
            "2": Region.CN_GF,
            "5": Region.CN_QD,
            "6": Region.USA,
            "7": Region.EURO,
            "8": Region.ASIA,
            "9": Region.CHT,
        }
        return region_dict.get(uid[0], Region.CN_GF)

    @staticmethod
    def get_by_str(val: str):
        for member in Region.__members__.values():
            if member.value == val:
                return member
        raise AssertionError(f"Param type error: [{val}].")
