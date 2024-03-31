import typing


class HsrException(Exception):
    """Base Exception"""

    msg = "There are some errors in the program."

    def __init__(self, msg: str = None, *args) -> None:
        self.msg = msg.format(*args) if msg else self.msg
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

    msg: str = "API调用异常"

    def __init__(self, response=None, msg: typing.Optional[str] = None) -> None:
        if response is None:
            response = {}
        self.retcode = response.get("retcode", self.retcode)
        self.original = response.get("message", "")

        self.msg = msg or self.msg or self.original

        super().__init__(f"[{self.retcode}] {self.msg}")

    def __repr__(self) -> str:
        response = {"retcode": self.retcode, "message": self.original}
        args = [repr(response)]
        if self.msg != self.original:
            args.append(repr(self.msg))

        return f"{self.__class__.__name__}({', '.join(args)})"


class InvalidLangError(ApiException):
    """未指定语言或不是支持的语言"""

    retcode = -108
    msg = "请求参数 lang 错误"


class InvalidCookieError(ApiException):
    retcode = -100
    msg = "请求参数 cookie 错误"


class VisitsTooFrequently(ApiException):
    retcode = -110
    msg = "访问过于频繁"


class InvalidGameBizError(ApiException):

    retcode = -111
    msg = "请求参数game_biz错误"


class AuthkeyExceptionError(ApiException):
    """"""

    retcode = -100
    msg = "Authkey 错误"


class InvalidAuthkeyError(AuthkeyExceptionError):
    """Authkey is not valid."""

    retcode = -100
    msg = "无效的Authkey"


class AuthkeyTimeoutError(AuthkeyExceptionError):
    """Authkey has timed out."""

    retcode = -101
    msg = "Authkey已过期"


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
            raise AuthkeyExceptionError(data)

    if retcode in _ERRORS:
        exc_type = _ERRORS[retcode]
        raise exc_type(data)

    raise ApiException(data)
