import functools
import traceback

from loguru import logger

from star_rail import exceptions as error


def error_handler(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            result = await func(self, *args, **kwargs)
        except error.ApiException as e:
            logger.debug(traceback.format_exc())
            self.notify(str(e), severity="warning")
            return
        except Exception as e:
            logger.debug(traceback.format_exc())
            self.notify(str(e), severity="error")
            return
        return result

    return wrapper


def required_account(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self.app.client.user is None:
            self.notify("请登陆账号后再试", severity="warning")
            return
        result = await func(self, *args, **kwargs)
        return result

    return wrapper
