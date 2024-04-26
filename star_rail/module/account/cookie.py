import typing
from http import cookies

from pydantic import BaseModel

from star_rail.module import routes
from star_rail.module.types import GameBiz
from star_rail.utils.logger import logger

from ..web import Header, request

__all__ = ["Cookie"]


def _parse_cookie(cookie: str) -> dict[str, str]:
    """cookie字符串解析为字典"""

    assert isinstance(cookie, str), f"Param type error. Expected type 'str', got [{type(cookie)}]."

    if not cookie:
        return {}

    simple_cookie = cookies.SimpleCookie(cookie)

    return {
        str(k): v.value if isinstance(v, cookies.Morsel) else str(v)
        for k, v in simple_cookie.items()
    }


class Cookie(BaseModel):
    account_id: str = ""
    account_id_v2: str = ""
    account_mid_v2: str = ""

    cookie_token: str = ""
    cookie_token_v2: str = ""

    login_ticket: str = ""
    login_uid: str = ""
    ltmid_v2: str = ""

    ltoken: str = ""
    ltoken_v2: str = ""
    ltuid: str = ""
    ltuid_v2: str = ""

    stoken: str = ""
    stuid: str = ""

    def __init__(self, **data):
        super().__init__(**data)

        self._init_mihoyo_uid()
        self._init_mihoyo_mid()

    def _init_mihoyo_uid(self):
        uid_params = (
            self.account_id,
            self.account_id_v2,
            self.stuid,
            self.login_uid,
            self.ltuid,
            self.ltuid_v2,
        )

        mihoyo_uid = self._get_first_non_empty_value(*uid_params)

        if mihoyo_uid:
            self.account_id = mihoyo_uid
            self.account_id_v2 = mihoyo_uid
            self.stuid = mihoyo_uid
            self.login_uid = mihoyo_uid
            self.ltuid = mihoyo_uid
            self.ltuid_v2 = mihoyo_uid

    def _init_mihoyo_mid(self):
        mid_params = (self.ltmid_v2, self.account_mid_v2)
        mid = self._get_first_non_empty_value(*mid_params)
        if mid:
            self.ltmid_v2 = mid
            self.account_mid_v2 = mid

    def _get_first_non_empty_value(self, *args):
        return next((v for v in args if v), None)

    @staticmethod
    def parse(cookie_str: str):
        cookie_dict = _parse_cookie(cookie_str)

        if not cookie_dict:
            return Cookie()

        logger.debug("parse cookie param:" + ",".join(k for k in cookie_dict.keys()))
        cookie = Cookie.model_validate(cookie_dict)
        return cookie

    def empty_stoken(self):
        return not bool(self.stoken and self.stuid)

    def empty_cookie_token(self):
        return not bool(self.cookie_token or self.cookie_token_v2)

    async def refresh_cookie_token(self, game_biz: GameBiz):
        """刷新 Cookie 的 cookie_token"""
        logger.debug("Refresh cookie_token.")

        data = await request(
            "GET",
            url=routes.COOKIE_TOKEN_BY_STOKEN_URL.get_url(game_biz),
            headers=Header.generate("WEB").headers,
            cookies=self.model_dump("web"),
            params={"uid": self.login_uid, "stoken": self.stoken},
        )
        self.cookie_token = data["cookie_token"]

    def update(self, cookie: "Cookie"):
        ck_dict = cookie.model_dump()
        for k, v in ck_dict.items():
            setattr(self, k, v)

    def model_dump(
        self, include: typing.Literal["all", "web", "ltoken", "stoken"] = "all", **kwargs
    ) -> dict[str, str]:
        """只输出有值的键值对

        Args:
            include (Literal["web", "ltoken", "stoken", "all"], optional):
                all: all
                web: login_ticket, login_uid, account_mid_v2, account_id, account_id_v2
                ltoken: ltoken, ltoken_v2, ltuid, ltuid_v2, ltmid_v2
                stoken: ltoken, ltoken_v2, ltuid, ltuid_v2, stoken, stuid
        """
        group = {
            "web": ["login_ticket", "login_uid", "account_mid_v2", "account_id", "account_id_v2"],
            "ltoken": ["ltoken", "ltoken_v2", "ltuid", "ltuid_v2", "ltmid_v2"],
            "stoken": ["ltoken", "ltoken_v2", "ltuid", "ltuid_v2", "ltmid_v2", "stoken", "stuid"],
        }
        if include not in group:
            return super().model_dump(exclude_defaults=True, **kwargs)
        return super().model_dump(include={*group[include]}, exclude_defaults=True, **kwargs)

    def __str__(self) -> str:
        return "; ".join([f"{key}={value}" for key, value in self.model_dump("all").items()])

    def empty(self):
        """为空返回True"""
        ck_dict = self.model_dump("all")
        return not bool(ck_dict)
