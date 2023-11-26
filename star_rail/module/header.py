import hashlib
import json
import random
import string
import time
import typing
from enum import Enum


class Header:
    _DEFAULT_APP_VERSION = "2.50.1"
    """默认的米游社 APP 版本，与下面 Salt 值对应"""

    class Salt(str, Enum):
        """对应 APP 版本 为 2.50.1

        数据来源 https://github.com/UIGF-org/mihoyo-api-collect/issues/1
        """

        K2 = "A4lPYtN0KGRVwE5M5Fm0DqQiC5VVMVM3"
        LK2 = "kkFiNdhyHqZ1VnDRHnU1podIvO4eiHcs"
        X4 = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
        X6 = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
        PROD = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"

    class RpcClientType(str, Enum):
        """x-rpc-client_type"""

        IOS = "1"
        ANDROID = "2"
        WEB = "4"
        PC = "5"

    class UserAgent(str, Enum):
        PC_WIN = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.41"
        )

        ANDROID = (
            "Mozilla/5.0 (Linux; Android 13; M2101K9C Build/TKQ1.220829.002; wv)"
            " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.5359.128"
            " Mobile Safari/537.36 miHoYoBBS/2.50.1"
        )

        IOS = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"
            " AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.50.1"
        )

    class Referer(str, Enum):
        APP_MIHOYO = "https://app.mihoyo.com"

        USER_MUHOYO = "https://user.mihoyo.com/"

        WEB_STATIC_MIHOYO = "https://webstatic.mihoyo.com/"

        WEB_STATIC_HOYOLAB = "https://webstatic-sea.hoyolab.com"

    class Origin(str, Enum):
        USER_MIHOYO = "https://user.mihoyo.com/"

        WEB_STATIC_MIHOYO = "https://webstatic.mihoyo.com/"

    def __init__(self) -> None:
        self._headers = {
            "Accept": "application/json",
        }

    def set_host(self, host):
        self._headers["Host"] = host

    def set_origin(self, origin: Origin):
        self._headers["Origin"] = origin.value

    def set_referer(self, referer: Referer):
        self._headers["Referer"] = referer.value

    def set_user_agent(self, user_agent: UserAgent):
        self._headers["User-Agent"] = user_agent.value

    def set_x_rpc_app_version(self, app_version: str = _DEFAULT_APP_VERSION):
        self._headers["x-rpc-app_version"] = app_version

    def set_x_rpc_client_type(self, client_type: RpcClientType):
        self._headers["x-rpc-client_type"] = client_type.value

    def set_ds(
        self,
        version: typing.Literal["v1", "v2"],
        salt: Salt,
        query_param: dict = None,
        body: dict = None,
    ):
        if version == "v2":
            ds = self.gen_ds_v2(salt, query_param, body)
        else:
            ds = self.gen_ds_v1(salt)

        self._headers["DS"] = ds

    def update(self, header: dict):
        self._headers.update(header)

    @property
    def value(self):
        return self._headers

    @staticmethod
    def create_header(client_type: typing.Literal["PC", "WEB", "ANDROID"]):
        web_header = {
            "Accept": "application/json",
            "Origin": Header.Origin.USER_MIHOYO,
            "Referer": Header.Referer.USER_MUHOYO,
            "User-Agent": Header.UserAgent.PC_WIN,
            "x-rpc-client_type": Header.RpcClientType.WEB,
        }

        android_header = {
            "Accept": "application/json",
            "Origin": Header.Origin.USER_MIHOYO,
            "Referer": Header.Referer.USER_MUHOYO,
            "User-Agent": Header.UserAgent.ANDROID,
            "x-rpc-client_type": Header.RpcClientType.ANDROID,
        }
        pc_header = {
            "Accept": "application/json",
            "Origin": Header.Origin.USER_MIHOYO,
            "Referer": Header.Referer.USER_MUHOYO,
            "User-Agent": Header.UserAgent.PC_WIN,
            "x-rpc-client_type": Header.RpcClientType.PC,
        }
        header = Header()
        if client_type == "WEB":
            header.update(web_header)
        elif client_type == "PC":
            header.update(pc_header)
        else:
            header.update(android_header)
        return header

    @staticmethod
    def _get_random_string(length: int):
        """生成只包含小写字母和数字的随机字符串"""
        return "".join(random.sample(string.ascii_lowercase + string.digits, length))

    @staticmethod
    def _gen_random_int_str():
        """生成长度为6的数字字符串"""
        return str(random.randint(100001, 200000))

    @staticmethod
    def _signature_with_md5(text: str):
        md5 = hashlib.md5()
        md5.update(text.encode())
        return md5.hexdigest()

    @staticmethod
    def gen_ds_v1(salt: Salt):
        """适用于 x-rpc-client_type = 2 (ClientType.Android)"""
        t = str(int(time.time()))
        r = Header._get_random_string(6)
        c = Header._signature_with_md5(f"salt={salt.value}&t={t}&r={r}")
        return f"{t},{r},{c}"

    @staticmethod
    def gen_ds_v2(salt: Salt, query_param: dict = None, body: dict = None):
        """适用于 x-rpc-client_type = 5 (ClientType.PC)

        Args:
            salt: salt
            query_param (dict, optional): api查询参数. Defaults to None.
            body (dict, optional): api请求体参数. Defaults to None.

        Returns:
            str: ds str
        """
        query_str = "&".join(f"{k}={v}" for k, v in sorted(query_param.items()))
        body_str = json.dumps(body) if body else ""
        t = str(int(time.time()))
        r = Header._gen_random_int_str()
        c = Header._signature_with_md5(f"salt={salt.value}&t={t}&r={r}&b={body_str}&q={query_str}")
        return f"{t},{r},{c}"
