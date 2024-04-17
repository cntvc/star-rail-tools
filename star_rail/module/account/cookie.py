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


def _remove_suffix(dict_: dict[str, str], suffix: str):
    """移除字典 key 的后缀"""
    length = len(suffix)
    d = {}
    for k, v in dict_.items():
        if k.endswith(suffix):
            d[k[:-length]] = v
        else:
            d[k] = v
    return d


class Cookie(BaseModel):
    login_ticket: str = ""
    login_uid: str = ""

    account_id: str = ""
    account_mid: str = ""

    ltoken: str = ""
    ltuid: str = ""
    ltmid: str = ""

    cookie_token: str = ""

    stoken: str = ""
    stuid: str = ""

    def __init__(self, **data):
        super().__init__(**data)

        self._init_mihoyo_uid()
        self._init_mihoyo_mid()

    def _init_mihoyo_uid(self):
        uid_params = (self.stuid, self.ltuid, self.login_uid, self.account_id)

        mihoyo_uid = self._get_first_non_empty_value(*uid_params)

        if mihoyo_uid:
            self.stuid = mihoyo_uid
            self.ltuid = mihoyo_uid
            self.login_uid = mihoyo_uid
            self.account_id = mihoyo_uid

    def _init_mihoyo_mid(self):
        mid_params = (self.ltmid, self.account_mid)
        mid = self._get_first_non_empty_value(*mid_params)
        if mid:
            self.ltmid = mid
            self.account_mid = mid

    def _get_first_non_empty_value(self, *args):
        return next((v for v in args if v), None)

    @staticmethod
    def parse(cookie_str: str):
        cookie_dict = _parse_cookie(cookie_str)

        if not cookie_dict:
            return Cookie()

        # 获取的 cookie 可能为 v2 版本，将后缀去除
        cookie_dict = _remove_suffix(cookie_dict, "_v2")

        logger.debug("parse cookie param:" + " ".join(k for k, _ in cookie_dict.items()))
        cookie = Cookie.model_validate(cookie_dict)
        return cookie

    def empty_login_ticket(self):
        return not bool(self.login_ticket and self.login_uid)

    def empty_stoken(self):
        return not bool(self.stoken and self.stuid)

    def empty_cookie_token(self):
        return not bool(self.cookie_token)

    async def refresh_multi_token(self, game_biz: GameBiz):
        """刷新 Cookie 的 stoken 和 ltoken"""
        logger.debug("Refresh stoken and ltoken.")
        params = {
            "login_ticket": self.login_ticket,
            "token_types": 3,
            "uid": self.login_uid,
        }
        data = await request(
            "GET",
            url=routes.MULTI_TOKEN_BY_LOGINTICKET_URL.get_url(game_biz),
            headers=Header.generate("WEB").headers,
            params=params,
        )
        token_data = data["list"]
        for item in token_data:
            if item["name"] == "stoken":
                self.stoken = item["token"]
            if item["name"] == "ltoken":
                self.ltoken = item["token"]

    async def refresh_cookie_token(self, game_biz: GameBiz):
        """刷新 Cookie 的 cookie_token"""
        logger.debug("Refresh cookie_token.")
        if game_biz == GameBiz.GLOBAL:
            # 暂由用户在网页抓取后手动更新
            return

        data = await request(
            "GET",
            url=routes.COOKIE_TOKEN_BY_STOKEN_URL.get_url(game_biz),
            headers=Header.generate("WEB").headers,
            cookies=self.model_dump("web"),
            params={"uid": self.login_uid, "stoken": self.stoken},
        )
        self.cookie_token = data["cookie_token"]

    def model_dump(
        self, include: typing.Literal["all", "web", "ltoken", "stoken"] = "all", **kwargs
    ) -> dict[str, str]:
        """只输出有值的键值对

        Args:
            include (Literal["web", "ltoken", "stoken", "all"], optional):
                all: all
                web: login_ticket, login_uid, account_mid, account_id
                ltoken: ltoken, ltuid, ltmid
                stoken: ltoken, ltuid, ltmid, stoken, stuid
        """
        group = {
            "web": ["login_ticket", "login_uid", "account_mid", "account_id"],
            "ltoken": ["ltoken", "ltuid", "ltmid"],
            "stoken": ["ltoken", "ltuid", "ltmid", "stoken", "stuid"],
        }
        if include not in group:
            return super().model_dump(exclude_defaults=True, **kwargs)
        return super().model_dump(include={*group[include]}, exclude_defaults=True, **kwargs)

    def __str__(self) -> str:
        return "; ".join([f"{key}={value}" for key, value in self.model_dump("all").items()])

    def __eq__(self, other: "Cookie"):
        return (
            self.login_uid == other.login_uid
            and self.login_ticket == other.login_ticket
            and self.cookie_token == other.cookie_token
            and self.ltoken == other.ltoken
            and self.stoken == other.stoken
        )

    def __ne__(self, other: "Cookie"):
        return (
            self.login_uid != other.login_uid
            or self.login_ticket != other.login_ticket
            or self.cookie_token != other.cookie_token
            or self.ltoken != other.ltoken
            or self.stoken != other.stoken
            or self.ltmid != other.ltmid
        )

    def empty(self):
        """为空返回True"""
        ck_dict = self.model_dump("all")
        return not bool(ck_dict)
