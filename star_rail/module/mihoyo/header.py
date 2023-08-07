import enum
import json
import random
import string
import time

from star_rail.utils.functional import signature_with_md5


class ClientType(str, enum.Enum):
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


class DynamicSecret:
    def __init__(self, salt_type: Salt) -> None:
        self.salt = salt_type.value

    def _get_random_string(self, only_number: bool = False):
        """生成长度为6的随机字符串

        Args:
            only_number (bool, optional): 是否仅包含数字. Defaults to False.

        Returns:
            str: 随机字符串
        """
        if only_number:
            return str(random.randint(100001, 200000))
        return "".join(random.sample(string.ascii_lowercase + string.digits, 6))

    def gen_ds_v1(self):
        """适用于 x-rpc-client_type = 2 (ClientType.Android)"""
        t = str(int(time.time()))
        r = self._get_random_string()
        c = signature_with_md5(f"salt={self.salt}&t={t}&r={r}")
        return f"{t},{r},{c}"

    def gen_ds_v2(self, query_param: dict = None, body: dict = None):
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
        r = self._get_random_string(True)
        c = signature_with_md5(f"salt={self.salt}&t={t}&r={r}&b={body_str}&q={query_str}")
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
        self.headers = {
            "Accept": "application/json",
        }
        self._has_client_type = False
        """是否设置了 x-rpc-client_type """

    def host(self, v):
        self.headers["Host"] = v
        return self

    def origin(self, v: Origin):
        self.headers["Origin"] = v.value
        return self

    def referer(self, v: Referer):
        self.headers["Referer"] = v.value
        return self

    def user_agent(self, v: UserAgent):
        self.headers["User-Agent"] = v.value
        return self

    def x_rpc_app_version(self, app_version: str = _DEFAULT_APP_VERSION):
        self.headers["x-rpc-app_version"] = app_version
        return self

    def x_rpc_client_type(self, client_type: ClientType):
        self.headers["x-rpc-client_type"] = client_type.value
        self._has_client_type = True
        return self

    def x_rpc_device_id(self, v):
        self.headers["x-rpc-device_id"] = v
        return self

    def x_requested_with(self, v: XRequestedWith):
        self.headers["X-Requested-With"] = v.value
        return self

    def ds(self, salt: Salt, query_param: dict = None, body: dict = None):
        if not self._has_client_type:
            raise ValueError("x-rpc-client_type 必须在设置 ds 前初始化")
        if self.headers["x-rpc-client_type"] == ClientType.PC:
            ds = DynamicSecret(salt).gen_ds_v2(query_param, body)
        elif self.headers["x-rpc-client_type"] == ClientType.ANDROID:
            ds = DynamicSecret(salt).gen_ds_v1()
        self.headers["DS"] = ds
        return self

    def build(self):
        return self.headers
