import typing


class HsrException(Exception):
    """Base Exception"""

    msg = "There are some errors in the program."

    def __init__(self, msg: str = None, *args) -> None:
        self.msg = msg.format(*args) if msg is not None else self.msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


class GachaRecordError(HsrException):
    pass


class MetadataError(HsrException):
    pass


############################################################
# Api Exception
############################################################


class ApiException(HsrException):
    """Network request exception"""

    retcode: int = 0

    original: str = ""

    msg: str = ""

    def __init__(self, response=None, msg: typing.Optional[str] = None) -> None:
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
    msg = "Invalid lang value."


class InvalidCookieError(ApiException):
    retcode = -100
    msg = "Invalid cookie value."


class VisitsTooFrequently(ApiException):
    retcode = -110
    msg = "Visits too frequently."


class InvalidGameBizError(ApiException):
    """请求参数game_biz不正确"""

    retcode = -111
    msg = "Invalid game_biz value."


class AuthkeyExceptionError(ApiException):
    """"""

    msg = "Invalid authkey value."


class InvalidAuthkeyError(AuthkeyExceptionError):
    """Authkey is not valid."""

    retcode = -100


class AuthkeyTimeoutError(AuthkeyExceptionError):
    """Authkey has timed out."""

    retcode = -101


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
        exception_type = _ERRORS[retcode]
        raise exception_type(data)

    raise ApiException(data)
