import functools
import traceback
import typing

from star_rail.utils.log import logger


class HsrException(Exception):
    """Base Exception"""

    msg = ""

    def __init__(self, msg: str = None, *args) -> None:
        self.msg = msg.format(*args) if msg is not None else self.msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


class DataBaseError(HsrException):
    pass


class EncryptError(HsrException):
    pass


class DecryptError(HsrException):
    pass


############################################################
# Api Exception
############################################################


class ApiException(HsrException):
    """Network request exception"""

    retcode: int = 0

    original: str = ""

    msg: str = ""

    def __init__(
        self,
        response=None,
        msg: typing.Optional[str] = None,
        *args,
    ) -> None:
        if response is None:
            response = {}
        self.retcode = response.get("retcode", self.retcode)
        self.original = response.get("message", "")
        self.msg = msg or self.msg.format(args) or self.original

        super().__init__(self.msg)

    def __str__(self) -> str:
        if self.retcode:
            return f"[{self.retcode}] {self.msg}"
        return self.msg


class RequestError(ApiException):
    msg = "network error"


class InvalidCookieError(ApiException):
    retcode = -100
    msg = "Invalid cookie value"


class AuthkeyExceptionError(ApiException):
    """"""

    msg = ""


class InvalidAuthkeyError(AuthkeyExceptionError):
    """Authkey is not valid."""

    retcode = -100
    msg = "InvalidAuthkey"


class AuthkeyTimeoutError(AuthkeyExceptionError):
    """Authkey has timed out."""

    retcode = -101
    msg = "InvalidAuthkey"


_ERRORS: dict[int, type[ApiException]] = {
    -100: InvalidCookieError,
    10001: InvalidCookieError,  # game record error
}


def raise_for_retcode(data: dict[str, typing.Any]) -> typing.NoReturn:
    """API请求的异常处理

    [跃迁记录]
        -100: invalid authkey
        -101:
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


def err_catch(
    exec_type: HsrException | typing.Tuple[HsrException, ...] = HsrException,
    level: typing.Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "ERROR",
):
    """捕获异常打印 msg 并返回 None"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exec_type as e:
                logger.log(level, e)
                logger.debug(traceback.format_exc())
                return None

        return wrapper

    return decorator
