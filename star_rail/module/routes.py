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

COOKIE_TOKEN_BY_STOKEN_URL = InternationalRoute(
    chinese="https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken",
    overseas="https://api-account-os.hoyoverse.com/account/auth/api/getCookieAccountInfoBySToken",
)
"""[Cookie] 通过 SToken 获取 cookie_token """


####################################################################
# 米游社api
####################################################################

MONTH_INFO_URL = InternationalRoute(
    chinese="https://api-takumi.mihoyo.com/event/srledger/month_info",
    overseas="https://sg-public-api.hoyolab.com/event/srledger/month_info",
)
"""[米游社] 开拓月历"""


####################################################################
# 跃迁记录
####################################################################

GACHA_LOG_URL = InternationalRoute(
    chinese="https://public-operation-hkrpg.mihoyo.com/common/gacha_record/api/getGachaLog",
    overseas="https://public-operation-hkrpg-sg.hoyoverse.com/common/gacha_record/api/getGachaLog",
)
"""[GameClient] 跃迁记录"""


__all__ = [name for name in dir() if name.endswith("_URL")]
