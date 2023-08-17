import typing
from http import cookies
from typing import Literal

from loguru import logger
from pydantic import BaseModel, model_validator

from .api_client import WEB_HEADER, request
from .routes import COOKIE_TOKEN_BY_STOKEN_URL, STOKEN_BY_LOGINTICKET_URL

__all__ = ["Cookie"]


class Cookie(BaseModel):
    login_ticket: str = ""
    login_uid: str = ""

    account_id: str = ""
    cookie_token: str = ""

    ltoken: str = ""
    ltuid: str = ""
    mid: str = ""
    """ 同 webapi: [ltmid_v2, account_mid_v2]"""
    stoken: str = ""
    stuid: str = ""

    @model_validator(mode="after")
    def reset_mid(self):
        """创建实例后初始化相同值的字段: mihoyo uid"""
        mihoyo_uid = None
        uid_params = (self.stuid, self.ltuid, self.login_uid, self.account_id)
        for v in uid_params:
            if v:
                mihoyo_uid = v
                break
        if mihoyo_uid is None:
            return self
        self.stuid = mihoyo_uid
        self.ltuid = mihoyo_uid
        self.login_uid = mihoyo_uid
        self.account_id = mihoyo_uid
        return self

    # TODO 校验stoken有效性
    # TODO stoken刷新其他cookie的接口
    @staticmethod
    def parse(cookie_str: str):
        cookie_dict = parse_cookie(cookie_str)

        if not cookie_dict:
            return None

        # 从网页版获取的 cookie 部分参数带有 _v2 后缀
        cookie_dict = remove_suffix(cookie_dict, "_v2")
        if "ltmid" in cookie_dict:
            cookie_dict["mid"] = cookie_dict["ltmid"]
        logger.debug("cookie param:" + " ".join(k for k, _ in cookie_dict.items()))
        cookie = Cookie.model_validate(cookie_dict)
        return cookie

    def verify_login_ticket(self):
        return self.login_ticket and self.login_uid and self.mid

    def verify_stoken(self):
        return self.stoken and self.stuid and self.mid

    def verify_cookie_token(self):
        return self.cookie_token and self.account_id

    def model_dump(self, include: Literal["web", "app", "all"] = "all"):
        """只输出有值的键值对

        Args:
            include (Literal['web', 'app', 'all'], optional):
                all: 包含所有
                web: web cookie
                app: 除 web cookie 外的参数
        """
        group = {
            "web": ["login_ticket", "login_uid"],
            "app": ["account_id", "cookie_token", "ltoken", "ltuid", "mid", "stoken", "stuid"],
        }
        if include not in group:
            include = "all"
        if include == "web":
            return super().model_dump(include={*group["web"]}, exclude_defaults=True)
        elif include == "app":
            return super().model_dump(include={*group["app"]}, exclude_defaults=True)
        else:
            return super().model_dump(exclude_defaults=True)

    def __str__(self) -> str:
        return "; ".join([f"{key}={value}" for key, value in self.model_dump("all").items()])

    def refresh_stoken_by_login_ticket(self):
        params = {
            "login_ticket": self.login_ticket,
            "token_types": 3,
            "uid": self.login_uid,
        }
        data = request(
            "get", url=STOKEN_BY_LOGINTICKET_URL.get_url(), headers=WEB_HEADER, params=params
        )
        data = data["list"]
        for item in data:
            if item["name"] == "stoken":
                self.stoken = item["token"]
            if item["name"] == "ltoken":
                self.ltoken = item["token"]

    def refresh_cookie_token_by_stoken(self):
        data = request(
            "get",
            COOKIE_TOKEN_BY_STOKEN_URL.get_url(),
            headers=WEB_HEADER,
            cookies=self.model_dump("web"),
            params={"uid": self.login_uid, "stoken": self.stoken},
        )
        self.cookie_token = data["cookie_token"]


def parse_cookie(cookie: str) -> typing.Dict[str, str]:
    """cookie字符串解析为字典"""
    if cookie is None:
        return {}
    if isinstance(cookie, str):
        cookie = cookies.SimpleCookie(cookie)

    return {str(k): v.value if isinstance(v, cookies.Morsel) else str(v) for k, v in cookie.items()}


def remove_suffix(dict_: dict, suffix: str):
    """移除字典 key 的后缀"""
    length = len(suffix)
    d = {}
    for k, v in dict_.items():
        if k.endswith(suffix):
            d[k[:-length]] = v
        else:
            d[k] = v
    return d
