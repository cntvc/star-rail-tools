from typing import Literal

import requests
from pydantic import BaseModel, model_validator

from star_rail.module.mihoyo.header import ClientType, Header, Origin, Referer, UserAgent
from star_rail.module.mihoyo.routes import COOKIE_TOKEN_BY_STOKEN_URL, STOKEN_BY_LOGINTICKET_URL


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
        uid_params = [self.stuid, self.ltuid, self.login_uid, self.account_id]
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

    @staticmethod
    def parse(cookie_str: str):
        """解析WebApi的cookie"""
        # TODO 支持米游社stoken解析
        cookie_dict = parse_cookie_str(cookie_str)

        if not cookie_dict:
            return None
        cookie_dict = remove_suffix(cookie_dict, "_v2")
        if "ltmid" in cookie_dict:
            cookie_dict["mid"] = cookie_dict["ltmid"]
        cookie = Cookie.model_validate(cookie_dict)
        return cookie

    def verify_login_ticket(self):
        return self.login_ticket and self.login_uid and self.mid

    def verify_stoken(self):
        return self.stoken and self.stuid and self.mid

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

    def set_stoken_by_login_ticket(self):
        params = {
            "login_ticket": self.login_ticket,
            "token_types": 3,
            "uid": self.login_uid,
        }
        header = (
            Header()
            .x_rpc_app_version()
            .user_agent(UserAgent.PC_WIN)
            .x_rpc_client_type(ClientType.PC)
            .referer(Referer.USER_MUHOYO)
            .origin(Origin.USER_MIHOYO)
            .build()
        )
        response = requests.get(
            url=STOKEN_BY_LOGINTICKET_URL.get_url(), headers=header, params=params
        ).json()

        if response["retcode"] != 0:
            """cookie 失效或其他"""
            return False
        data = response["data"]["list"]
        for item in data:
            if item["name"] == "stoken":
                self.stoken = item["token"]
            if item["name"] == "ltoken":
                self.ltoken = item["token"]
        return True

    def set_cookie_token_by_stoken(self):
        header = (
            Header()
            .x_rpc_app_version()
            .user_agent(UserAgent.PC_WIN)
            .x_rpc_client_type(ClientType.PC)
            .referer(Referer.USER_MUHOYO)
            .origin(Origin.USER_MIHOYO)
            .build()
        )

        res = requests.get(
            COOKIE_TOKEN_BY_STOKEN_URL.get_url(),
            headers=header,
            cookies=self.model_dump("web"),
            params={"uid": self.login_uid, "stoken": self.stoken},
        ).json()
        data = res["data"]
        self.cookie_token = data["cookie_token"]
        return True


def parse_cookie_str(cookie_str: str):
    """cookie字符串解析为字典"""
    cookies = {}
    if cookie_str:
        cookie_pairs = cookie_str.split(";")
        for pair in cookie_pairs:
            key, value = pair.strip().split("=", 1)
            cookies[key] = value
    return cookies


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
