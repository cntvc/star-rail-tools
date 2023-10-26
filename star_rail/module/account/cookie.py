from http import cookies
from typing import Literal

from pydantic import BaseModel, model_validator

from star_rail import exceptions as error
from star_rail.utils.log import logger

from ..api_helper import DefaultHeader, request
from ..routes import COOKIE_TOKEN_BY_STOKEN_URL, MULTI_TOKEN_BY_LOGINTICKET_URL
from ..types import GameBiz

__all__ = ["Cookie"]


class Cookie(BaseModel):
    login_ticket: str = ""
    login_uid: str = ""

    account_id: str = ""
    cookie_token: str = ""

    ltoken: str = ""
    ltuid: str = ""
    mid: str = ""
    """mihoyo uid

    同 webapi: [ltmid_v2, account_mid_v2]
    """

    stoken: str = ""
    stuid: str = ""

    @model_validator(mode="after")
    def init_uid(self):
        """创建实例后初始化相同值的字段"""

        uid_params = (self.stuid, self.ltuid, self.login_uid, self.account_id)

        mihoyo_uid = next((v for v in uid_params if v), None)

        if mihoyo_uid:
            self.stuid = mihoyo_uid
            self.ltuid = mihoyo_uid
            self.login_uid = mihoyo_uid
            self.account_id = mihoyo_uid
        return self

    @staticmethod
    def parse(cookie_str: str):
        cookie_dict = _parse_cookie(cookie_str)

        if not cookie_dict:
            raise error.HsrException("Invalid cookie value, {}", cookie_dict)

        # 获取的 cookie 可能为 v2 版本，特征为部分 key 名称后缀为 '_v2'，这里统一去除后缀
        cookie_dict = _remove_suffix(cookie_dict, "_v2")
        # 一般接口只使用到了 mid 值，但是来源有多个，例如 'ltmid'
        if "ltmid" in cookie_dict:
            cookie_dict["mid"] = cookie_dict["ltmid"]

        logger.debug("parse cookie param:" + " ".join(k for k, _ in cookie_dict.items()))
        cookie = Cookie.model_validate(cookie_dict)
        return cookie

    def verify_login_ticket(self):
        return True if self.login_ticket and self.login_uid else False

    def verify_stoken(self):
        return True if self.stoken and self.stuid and self.mid else False

    def verify_cookie_token(self):
        return True if self.cookie_token and self.account_id else False

    def model_dump(
        self, include: Literal["all", "web", "ltoken", "stoken"] = "all", *args, **kwargs
    ) -> dict[str, str]:
        """只输出有值的键值对

        Args:
            include (Literal["web", "ltoken", "stoken", "all"], optional):
                all: all
                web: login_ticket + login_uid
                ltoken: ltoken
                stoken: ltoken + stoken
        """
        group = {
            "web": ["login_ticket", "login_uid"],
            "ltoken": ["ltoken", "ltuid", "mid"],
            "stoken": ["ltoken", "ltuid", "mid", "stoken", "stuid"],
        }
        if include not in group:
            return super().model_dump(exclude_defaults=True)
        return super().model_dump(include={*group[include]}, exclude_defaults=True)

    def __str__(self) -> str:
        return "; ".join([f"{key}={value}" for key, value in self.model_dump("all").items()])

    def refresh_multi_token(self):
        """刷新 stoken 和 ltoken"""
        logger.debug("refresh multi cookie, uid: ", self.login_uid)
        params = {
            "login_ticket": self.login_ticket,
            "token_types": 3,
            "uid": self.login_uid,
        }
        data = request(
            "get",
            url=MULTI_TOKEN_BY_LOGINTICKET_URL.get_url(),
            headers=DefaultHeader.WEB_HEADER,
            params=params,
        )
        data = data["list"]
        for item in data:
            if item["name"] == "stoken":
                self.stoken = item["token"]
            if item["name"] == "ltoken":
                self.ltoken = item["token"]

    def refresh_cookie_token(self):
        """刷新 cookie_token"""
        logger.debug("refresh cookie_token, uid: ", self.login_uid)
        data = request(
            "get",
            COOKIE_TOKEN_BY_STOKEN_URL.get_url(GameBiz.get_by_uid(self.login_uid)),
            headers=DefaultHeader.WEB_HEADER,
            cookies=self.model_dump("web"),
            params={"uid": self.login_uid, "stoken": self.stoken},
        )
        self.cookie_token = data["cookie_token"]

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
        )

    def is_empty(self):
        cookie_dict = self.model_dump()
        return False if cookie_dict else True


def _parse_cookie(cookie: str) -> dict[str, str]:
    """cookie字符串解析为字典"""
    if cookie is None:
        return {}
    if isinstance(cookie, str):
        simple_cookie = cookies.SimpleCookie(cookie)
    else:
        raise error.HsrException("Param type error, type: {}", type(cookie))

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
