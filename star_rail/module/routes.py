import abc
import typing

from star_rail.module.account import GameBizType


class BaseRoute(abc.ABC):
    pass


class Route(BaseRoute):
    url: str

    def __init__(self, url: str) -> None:
        self.url = url

    def get_url(self):
        return self.url


class InternationalRoute(BaseRoute):
    urls: typing.Mapping[GameBizType, str]

    def __init__(self, overseas: str, chinese: str) -> None:
        self.urls = {
            GameBizType.GLOBAL: overseas,
            GameBizType.CN: chinese,
        }

    def get_url(self, game_biz: GameBizType):
        if not self.urls[game_biz]:
            raise ValueError(f"URL does not support {game_biz.name} region.")
        return self.urls[game_biz]


TAKUMI_URL = InternationalRoute(
    overseas="https://api-os-takumi.mihoyo.com/",
    chinese="https://api-takumi.mihoyo.com/",
)

GACHA_LOG_URL = InternationalRoute(
    overseas=f"{TAKUMI_URL.get_url(GameBizType.GLOBAL)}common/gacha_record/api/getGachaLog",
    chinese=f"{TAKUMI_URL.get_url(GameBizType.CN)}common/gacha_record/api/getGachaLog",
)
