import typing


class HsrException(Exception):
    """Base Exception"""

    msg = "程序出现未知错误"

    def __init__(self, msg: str = None, *args) -> None:
        self.msg = msg.format(*args) if msg is not None else self.msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


class GachaRecordError(HsrException):
    pass


############################################################
# Api Exception
############################################################


class ApiException(HsrException):
    """Network request exception"""

    retcode: int = 0

    original: str = ""

    msg: str = "Api 请求异常"

    def __init__(self, response=None, msg: str | None = None) -> None:
        if response is None:
            response = {}
        self.retcode = response.get("retcode", self.retcode)
        self.original = response.get("message", "")

        self.msg = msg or self.msg or self.original

        super().__init__(self.msg)

    def __repr__(self) -> str:
        response = {"retcode": self.retcode, "message": self.original}
        args = [repr(response)]
        if self.msg != self.original:
            args.append(repr(self.msg))

        return f"{self.__class__.__name__}({', '.join(args)})"

    def __str__(self) -> str:
        return self.__repr__()


class InvalidLangError(ApiException):
    """未指定语言或不是支持的语言"""

    retcode = -108
    msg = "语言参数错误"


class InvalidCookieError(ApiException):
    retcode = -100
    msg = "无效的 cookie "


class VisitsTooFrequently(ApiException):
    retcode = -110
    msg = "访问过于频繁"


class InvalidGameBizError(ApiException):
    """请求参数game_biz不正确"""

    retcode = -111
    msg = "game_biz 参数错误"


class AuthkeyError(ApiException):
    """"""

    msg = "无效的 authkey"


class InvalidAuthkeyError(AuthkeyError):
    """Authkey is not valid."""

    retcode = -100


class AuthkeyTimeoutError(AuthkeyError):
    """Authkey has timed out."""

    retcode = -101
    msg = "authkey 已过期"


_ERRORS: dict[int, type[ApiException]] = {
    -108: InvalidLangError,
    -100: InvalidCookieError,
    10001: InvalidCookieError,  # game record error
    -110: VisitsTooFrequently,
    -111: InvalidGameBizError,
}


def raise_for_retcode(data: dict[str, typing.Any]) -> typing.NoReturn:
    """API请求的异常处理

    [跃迁记录]
        -100: invalid authkey
        -101: invalid authkey
        -111: game_biz error
    [cookie]
        -100: cookie 失效
    """
    retcode = data.get("retcode", 0)
    message = data.get("message", "")

    if message.startswith("authkey"):
        if retcode == -100:
            raise InvalidAuthkeyError(data)
        elif retcode == -101:
            raise AuthkeyTimeoutError(data)
        else:
            raise AuthkeyError(data)

    if retcode in _ERRORS:
        exception_type = _ERRORS[retcode]
        raise exception_type(data)

    raise ApiException(data)
