import asyncio
import functools
import json
import typing

import aiohttp
import yarl

from star_rail import exceptions
from star_rail.utils.logger import logger

_CallableT = typing.TypeVar("_CallableT", bound=typing.Callable[..., typing.Awaitable[typing.Any]])

__all__ = ["request", "_request"]


def replace_params_values(params: dict, param_names_to_replace: list, placeholder: str) -> dict:
    """
    Replace values of specified parameters in the dictionary with a placeholder.

    Args:
        params (dict): The parameter dictionary.
        param_names_to_replace (list): List of parameter names to replace.
        placeholder (str): The placeholder value.

    Returns:
        dict: The updated parameter dictionary.
    """
    return {k: placeholder if k in param_names_to_replace else v for k, v in params.items()}


async def _request_hook(
    method: typing.Literal["GET", "POST"],
    url: yarl.URL,
    params: dict[str, str] = None,
    data: dict[str, str] = None,
    **kwargs,
) -> None:
    log_url = url
    if params:
        log_url = url.update_query(replace_params_values(params, ["authkey"], "***"))
    logger.debug(
        "[{}] {} {}",
        method,
        log_url,
        "\ndata: " + json.dumps(data, separators=(",", ":")) if data else "",
    )


async def _request(
    method: typing.Literal["GET", "POST"],
    url: yarl.URL,
    params: dict[str, str] = None,
    data: dict[str, str] = None,
    cookies: dict[str, str] = None,
    headers: dict[str, str] = None,
    **kwargs,
) -> dict[str, str]:
    """Default request"""
    await _request_hook(method, url, params, data, **kwargs)

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            cookies=cookies,
            headers=headers,
            **kwargs,
        ) as response:
            data = await response.json()

    return data


def handle_rate_limits(
    exception: typing.Type[exceptions.HsrException] = exceptions.VisitsTooFrequently,
    *,
    tries: int = 5,
    delay: float = 0.3,
    max_delay: float = 5,
    factor: float = 2.0,
) -> typing.Callable[[_CallableT], _CallableT]:
    """Handle rate limits for requests."""

    def wrapper(func: typing.Callable[..., typing.Awaitable[typing.Any]]) -> typing.Any:
        @functools.wraps(func)
        async def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            current_delay = delay
            for _ in range(tries):
                try:
                    x = await func(*args, **kwargs)
                except exception:
                    await asyncio.sleep(current_delay)
                    # 请求出错，正在重试
                    current_delay = min(factor * current_delay, max_delay)
                else:
                    return x
            else:
                raise exception(f"Got rate limited {tries} times in a row.")

        return inner

    return wrapper


@handle_rate_limits()
async def request(
    method: typing.Literal["GET", "POST"],
    url: yarl.URL,
    params: dict[str, str] = None,
    data: dict[str, str] = None,
    cookies: dict[str, str] = None,
    headers: dict[str, str] = None,
    **kwargs,
) -> dict[str, str]:
    """Mihoyo API request"""
    data = await _request(method, url, params, data, cookies, headers, **kwargs)

    if "retcode" in data:
        if data["retcode"] == 0:
            return data["data"]
        exceptions.raise_for_retcode(data)
    return data
