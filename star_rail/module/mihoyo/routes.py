import abc
import typing

from star_rail.exceptions import ParamValueError

from .types import GameBiz


class BaseRoute(abc.ABC):
    pass


class Route(BaseRoute):
    url: str

    def __init__(self, url: str) -> None:
        self.url = url

    def get_url(self):
        return self.url


class InternationalRoute(BaseRoute):
    urls: typing.Mapping[GameBiz, str]

    def __init__(self, overseas: str, chinese: str) -> None:
        self.urls = {
            GameBiz.GLOBAL: overseas,
            GameBiz.CN: chinese,
        }

    def get_url(self, game_biz: GameBiz):
        if not self.urls[game_biz]:
            # 不会触发
            raise ParamValueError(f"URL does not support {game_biz.name} game_biz.")
        return self.urls[game_biz]


TAKUMI_HOST = InternationalRoute(
    overseas="https://api-os-takumi.mihoyo.com",
    chinese="https://api-takumi.mihoyo.com",
)

TAKUMI_RECORD_HOST = Route("https://api-takumi-record.mihoyo.com")

HOYOLAB_HOST = Route("https://bbs-api-os.hoyolab.com")
"""海外版米游社"""


GACHA_LOG_URL = InternationalRoute(
    overseas=f"{TAKUMI_HOST.get_url(GameBiz.GLOBAL)}/common/gacha_record/api/getGachaLog",
    chinese=f"{TAKUMI_HOST.get_url(GameBiz.CN)}/common/gacha_record/api/getGachaLog",
)
"""[GameClient] 跃迁记录"""


# 账号Cookie相关

STOKEN_BY_LOGINTICKET_URL = Route(
    "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket"
)
"""通过 login_ticket 获取 stoken """

COOKIE_TOKEN_BY_STOKEN_URL = Route(
    "https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken"
)
"""通过 SToken 获取 cookie_token """


# 米游社api

GAME_RECORD_CARD_URL = InternationalRoute(
    overseas=f"{HOYOLAB_HOST.get_url()}/game_record/card/wapi/getGameRecordCard",
    chinese=f"{TAKUMI_RECORD_HOST.get_url()}/game_record/card/wapi/getGameRecordCard",
)
"""[米游社] 获取游戏角色信息"""

MONTH_INFO_URL = Route(f"{TAKUMI_HOST.get_url(GameBiz.CN)}/event/srledger/month_info")
"""[米游社] 开拓月历"""

MONTH_DETAIL_URL = Route(f"{TAKUMI_HOST.get_url(GameBiz.CN)}/event/srledger/month_detail")
"""[米游社] 开拓月历详情"""

__all__ = [name for name in dir() if name.endswith("_URL")]
