import abc
import typing

import yarl

from star_rail.module.types import GameBiz


class BaseRoute(abc.ABC):  # ruff: ignore=B024
    pass


class Route(BaseRoute):
    url: yarl.URL

    def __init__(self, url: str) -> None:
        self.url = yarl.URL(url)

    def get_url(self) -> yarl.URL:
        return self.url


class InternationalRoute(BaseRoute):
    urls: typing.Mapping[GameBiz, yarl.URL]

    def __init__(
        self,
        chinese: str,
        overseas: str,
    ) -> None:
        self.urls = {
            GameBiz.CN: yarl.URL(chinese),
            GameBiz.GLOBAL: yarl.URL(overseas),
        }

    def get_url(self, game_biz: GameBiz) -> yarl.URL:
        return self.urls[game_biz]


####################################################################
# 账号Cookie相关
####################################################################

MULTI_TOKEN_BY_LOGINTICKET_URL = InternationalRoute(
    chinese="https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket",
    overseas="https://api-account-os.hoyoverse.com/account/auth/api/getMultiTokenByLoginTicket",
)
"""[Cookie] 通过 login_ticket 获取多类型 cookie 值"""

COOKIE_TOKEN_BY_STOKEN_URL = InternationalRoute(
    chinese="https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken",
    overseas="https://api-account-os.hoyoverse.com/account/auth/api/getCookieAccountInfoBySToken",
)
"""[Cookie] 通过 SToken 获取 cookie_token """


LTOKEN_BY_STOKEN_URL = InternationalRoute(
    chinese="https://passport-api.mihoyo.com/account/auth/api/getLTokenBySToken",
    overseas="https://api-account-os.hoyoverse.com/account/auth/api/getLTokenBySToken",
)
"""[Cookie] 通过 SToken 获取 Ltoken"""

####################################################################
# 米游社api
####################################################################

GAME_RECORD_CARD_URL = InternationalRoute(
    chinese="https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard",
    overseas="https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard",
)
"""[米游社] 获取游戏角色信息"""

MONTH_INFO_URL = InternationalRoute(
    chinese="https://api-takumi.mihoyo.com/event/srledger/month_info",
    overseas="https://sg-public-api.hoyolab.com/event/srledger/month_info",
)
"""[米游社] 开拓月历"""

MONTH_DETAIL_URL = InternationalRoute(
    chinese="https://api-takumi.mihoyo.com/event/srledger/month_detail",
    overseas="https://sg-public-api.hoyolab.com/event/srledger/month_detail",
)
"""[米游社] 开拓月历详情"""

####################################################################
# 跃迁记录
####################################################################

GACHA_LOG_URL = InternationalRoute(
    chinese="https://api-takumi.mihoyo.com/common/gacha_record/api/getGachaLog",
    overseas="https://api-os-takumi.mihoyo.com/common/gacha_record/api/getGachaLog",
)
"""[GameClient] 跃迁记录"""


__all__ = [name for name in dir() if name.endswith("_URL")]
