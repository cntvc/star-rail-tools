import functools
import traceback
import typing

from loguru import logger

from star_rail.i18n import i18n


class HsrException(Exception):
    msg = ""

    def __init__(self, msg: str = None, *args) -> None:
        self.msg = msg.format(*args) if msg is not None else self.msg
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg


class ParamValueError(HsrException):
    """参数值错误"""


class ParamTypeError(HsrException):
    """参数类型错误"""


class DataBaseError(HsrException):
    """数据库错误"""


class DataBaseModelError(DataBaseError):
    msg = "数据库模型错误"


class DataBaseConnectionError(DataBaseError):
    """数据库连接错误"""

    msg = i18n.error.db_conn_error


class DataBaseExecuteError(DataBaseError):
    msg = "数据库执行错误"


class DataError(HsrException):
    pass


class UnFoundFileError(HsrException):
    pass


############################################################
# Api Exception
############################################################


class ApiException(HsrException):
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
    msg = i18n.error.request_error


class InvalidCookieError(ApiException):
    retcode = -100
    msg = i18n.error.invalid_cookie_error


class AuthkeyExceptionError(ApiException):
    """"""

    msg = i18n.error.authkey_error


class InvalidAuthkeyError(AuthkeyExceptionError):
    """Authkey is not valid."""

    retcode = -100
    msg = i18n.error.invalid_authkey_error


class AuthkeyTimeoutError(AuthkeyExceptionError):
    """Authkey has timed out."""

    retcode = -101
    msg = i18n.error.invalid_authkey_error


_ERRORS: typing.Dict[int, typing.Type[ApiException]] = {
    -100: InvalidCookieError,
    10001: InvalidCookieError,  # game record error
}


def raise_for_retcode(data: typing.Dict[str, typing.Any]) -> typing.NoReturn:
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


def exec_catch(
    exec_type: typing.Union[HsrException, typing.Tuple[HsrException, ...]] = HsrException,
    level: typing.Literal["debug", "info", "warning", "error"] = "error",
):
    """捕获异常打印 msg 并返回 None"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exec_type as e:
                if level == "debug":
                    logger.debug(e)
                elif level == "info":
                    logger.info(e)
                elif level == "warning":
                    logger.warning(e)
                elif level == "error":
                    logger.error(e)
                logger.debug(traceback.format_exc())
                return None

        return wrapper

    return decorator
