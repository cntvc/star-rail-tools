import enum
import hashlib
import json
import random
import string
import time
import typing

import requests

from star_rail import constants
from star_rail import exceptions as error

__all__ = [
    "request",
    "RpcClientType",
    "Salt",
    "UserAgent",
    "Referer",
    "Origin",
    "XRequestedWith",
    "Header",
    "WEB_HEADER",
    "ANDROID_HEADER",
    "PC_HEADER",
]


def request(
    method: typing.Literal["get", "post"],
    url: str,
    params: typing.Dict[str, typing.Any] = None,
    cookies: typing.Dict[str, str] = None,
    headers: typing.Dict[str, str] = None,
    body: typing.Dict[str, typing.Any] = None,
    timeout=constants.REQUEST_TIMEOUT,
    **kwargs,
):
    with requests.request(
        method=method,
        url=url,
        params=params,
        cookies=cookies,
        headers=headers,
        data=body,
        timeout=timeout,
        **kwargs,
    ) as response:
        # TODO i18n
        r = response.headers.get("content-type")
        if r != "application/json":
            raise error.ApiException(
                msg="Recieved a response with an invalid content type:\n" + response.text
            )

        data = response.json()

    if data["retcode"] == 0:
        return data["data"]
    error.raise_for_retcode(data)


class RpcClientType(str, enum.Enum):
    """x-rpc-client_type"""

    IOS = "1"
    ANDROID = "2"
    Web = "4"
    PC = "5"


_DEFAULT_APP_VERSION = "2.50.1"


class Salt(str, enum.Enum):
    """对应 APP 版本 为 2.50.1

    数据来自于 https://github.com/UIGF-org/mihoyo-api-collect/issues/1
    """

    K2 = "A4lPYtN0KGRVwE5M5Fm0DqQiC5VVMVM3"
    LK2 = "kkFiNdhyHqZ1VnDRHnU1podIvO4eiHcs"
    X4 = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    X6 = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    PROD = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"


def get_random_string(length):
    """生成只包含小写字母和数字的随机字符串"""
    return "".join(random.sample(string.ascii_lowercase + string.digits, length))


def gen_random_int_str():
    """生成长度为6的数字字符串"""
    return str(random.randint(100001, 200000))


def gen_ds_v1(salt: Salt):
    """适用于 x-rpc-client_type = 2 (ClientType.Android)"""
    t = str(int(time.time()))
    r = get_random_string(6)
    c = signature_with_md5(f"salt={salt.value}&t={t}&r={r}")
    return f"{t},{r},{c}"


def gen_ds_v2(salt: Salt, query_param: dict = None, body: dict = None):
    """适用于 x-rpc-client_type = 5 (ClientType.PC)

    Args:
        query_param (dict, optional): api查询参数. Defaults to None.
        body (dict, optional): api请求体参数. Defaults to None.

    Returns:
        str: ds str
    """
    query_str = "&".join(f"{k}={v}" for k, v in sorted(query_param.items()))
    body_str = json.dumps(body) if body else ""
    t = str(int(time.time()))
    r = gen_random_int_str()
    c = signature_with_md5(f"salt={salt.value}&t={t}&r={r}&b={body_str}&q={query_str}")
    return f"{t},{r},{c}"


class UserAgent(str, enum.Enum):
    PC_WIN = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.41"
    )

    ANDROID = (
        "Mozilla/5.0 (Linux; Android 13; M2101K9C Build/TKQ1.220829.002; wv)"
        " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.5359.128"
        f" Mobile Safari/537.36 miHoYoBBS/{_DEFAULT_APP_VERSION}"
    )

    IOS = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)"
        f" AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/{_DEFAULT_APP_VERSION}"
    )


class Referer(str, enum.Enum):
    APP_MIHOYO = "https://app.mihoyo.com"

    USER_MUHOYO = "https://user.mihoyo.com/"

    WEB_STATIC_MIHOYO = "https://webstatic.mihoyo.com/"

    WEB_STATIC_HOYOLAB = "https://webstatic-sea.hoyolab.com"


class Origin(str, enum.Enum):
    USER_MIHOYO = "https://user.mihoyo.com/"

    WEB_STATIC_MIHOYO = "https://webstatic.mihoyo.com/"


class XRequestedWith(str, enum.Enum):
    CN = "com.mihoyo.hyperion"
    OS = "com.mihoyo.hoyolab"


class Header:
    def __init__(self) -> None:
        self._headers = {
            "Accept": "application/json",
        }

    def set_host(self, v):
        self._headers["Host"] = v

    def set_origin(self, v: Origin):
        self._headers["Origin"] = v.value

    def set_referer(self, v: Referer):
        self._headers["Referer"] = v.value

    def set_user_agent(self, v: UserAgent):
        self._headers["User-Agent"] = v.value

    def set_x_rpc_app_version(self, app_version: str = _DEFAULT_APP_VERSION):
        self._headers["x-rpc-app_version"] = app_version

    def set_x_rpc_client_type(self, client_type: RpcClientType):
        self._headers["x-rpc-client_type"] = client_type.value
        self._has_client_type = True

    def set_x_rpc_device_id(self, v):
        self._headers["x-rpc-device_id"] = v

    def set_x_requested_with(self, v: XRequestedWith):
        self._headers["X-Requested-With"] = v.value

    def set_ds(
        self,
        version: typing.Literal["v1", "v2"],
        salt: Salt,
        query_param: dict = None,
        body: dict = None,
    ):
        if version == "v2":
            ds = gen_ds_v2(salt, query_param, body)
        elif version == "v1":
            ds = gen_ds_v1(salt)
        else:
            raise error.ParamValueError("unsupported version, [{}]", version)
        self._headers["DS"] = ds

    def update(self, h: dict):
        self._headers.update(h)

    def dict(self):
        return self._headers


WEB_HEADER = {
    "Accept": "application/json",
    "Origin": Origin.USER_MIHOYO,
    "Refere": Referer.USER_MUHOYO,
    "User-Agent": UserAgent.PC_WIN,
    "x-rpc-client_type": RpcClientType.Web,
}
"""Web 请求头预设"""


ANDROID_HEADER = {
    "Accept": "application/json",
    "Origin": Origin.USER_MIHOYO,
    "Refere": Referer.USER_MUHOYO,
    "User-Agent": UserAgent.ANDROID,
    "x-rpc-client_type": RpcClientType.ANDROID,
}
"""android 请求头预设"""


PC_HEADER = {
    "Accept": "application/json",
    "Origin": Origin.USER_MIHOYO,
    "Refere": Referer.USER_MUHOYO,
    "User-Agent": UserAgent.PC_WIN,
    "x-rpc-client_type": RpcClientType.PC,
}


def signature_with_md5(text: str):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()


def generate_seed(length: int):
    characters = "0123456789abcdef"
    result = "".join(random.choices(characters, k=length))
    return result
